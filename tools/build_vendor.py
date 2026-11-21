#!/usr/bin/env python3
"""Assemble the hybrid X6532C vendor tree and emit exact metadata tables.

Inputs (produced from the stock erofs vendor image):
  fsmeta.tsv   <relpath>\t<uid>\t<gid>\t<mode-octal>
  labels.tsv   <relpath>\t<selinux-context>

The arm64 GPU stack from ../hybrid is grafted in, inheriting the identity of
its 32-bit twin where one exists (same owner, mode and SELinux type).
"""
import os, re, shutil, sys

BASE = '/home/randyyy/x6532c-work'
STOCK = os.path.join(BASE, 'stockimg')
STAGE = os.path.join(BASE, 'hybrid')
WORK = os.path.join(BASE, 'hybridimg')
ROOT = os.path.join(WORK, 'root')

meta = {}
for line in open(os.path.join(STOCK, 'fsmeta.tsv')):
    p, uid, gid, mode = line.rstrip('\n').split('\t')
    meta[p] = (int(uid), int(gid), int(mode, 8))

labels = {}
for line in open(os.path.join(STOCK, 'labels.tsv')):
    p, ctx = line.rstrip('\n').split('\t')
    labels[p] = ctx

# 1. fresh copy of the stock tree
if os.path.exists(ROOT):
    shutil.rmtree(ROOT)
shutil.copytree(os.path.join(STOCK, 'vendorstock'), ROOT, symlinks=True)

# 2. graft the 64-bit stack
added = []
for dirpath, dirnames, filenames in os.walk(STAGE):
    rel = os.path.relpath(dirpath, STAGE)
    base = '' if rel == '.' else rel
    for d in dirnames:
        dst = os.path.join(ROOT, base, d)
        if not os.path.isdir(dst):
            os.makedirs(dst)
            added.append(os.path.join(base, d))
    for f in filenames:
        src = os.path.join(dirpath, f)
        dst = os.path.join(ROOT, base, f)
        if os.path.lexists(dst):
            print('SKIP (sudah ada):', os.path.join(base, f))
            continue
        if os.path.islink(src):
            os.symlink(os.readlink(src), dst)
        else:
            shutil.copy2(src, dst, follow_symlinks=False)
        added.append(os.path.join(base, f))

# 3. identity for new entries, inherited from the 32-bit twin
SPH = 'u:object_r:same_process_hal_file:s0'
VND = 'u:object_r:vendor_file:s0'
VHL = 'u:object_r:vendor_hal_file:s0'

EXTRA_LABEL = {
    'lib64/hw/vulkan.mt6765.so': SPH,
    'lib64/hw': VHL,
    'lib64': VND,
    'lib64/egl': SPH,
}

unmatched = []
for p in added:
    twin = None
    if p.startswith('lib64/'):
        twin = 'lib/' + p[len('lib64/'):]
    if twin and twin in meta:
        uid, gid, mode = meta[twin]
        labels[p] = labels[twin]
        meta[p] = (uid, gid, mode)
        continue
    if os.path.islink(os.path.join(ROOT, p)):
        meta[p] = (0, 0, 0o777)
    elif os.path.isdir(os.path.join(ROOT, p)):
        meta[p] = (0, 2000, 0o755)
    else:
        meta[p] = (0, 0, 0o644)
    if p in EXTRA_LABEL:
        labels[p] = EXTRA_LABEL[p]
    else:
        labels[p] = SPH if '/egl/' in p or 'gralloc' in p or 'vulkan' in p else VND
        unmatched.append(p)

# 4. hand the tables to the caller
with open(os.path.join(WORK, 'meta.tsv'), 'w') as f:
    for p in sorted(meta):
        uid, gid, mode = meta[p]
        f.write('%s\t%d\t%d\t%04o\n' % (p, uid, gid, mode))

def esc(s):
    return re.sub(r'([.^$*+?()\[\]{}|\\])', r'\\\1', s)

with open(os.path.join(WORK, 'file_contexts'), 'w') as f:
    for p in sorted(labels):
        f.write('/vendor/%s %s\n' % (esc(p), labels[p]))

# Literal (unescaped) variant consumed by the patched mkfs.erofs lookup.
with open(os.path.join(WORK, 'labels_map.txt'), 'w') as f:
    f.write('/vendor %s\n' % VND)
    f.write('/vendor/ %s\n' % VND)
    for p in sorted(labels):
        f.write('/vendor/%s %s\n' % (p, labels[p]))

print('entri total :', len(meta))
print('ditambahkan :', len(added))
print('label unik  :', len(set(labels.values())))
for p in unmatched:
    print('  label tebakan:', p, labels[p])