#!/usr/bin/env python3
"""End to end verification of the rebuilt hybrid vendor image.

Checks, for every entry reachable in the mounted image:
  * SELinux label  vs the label map taken from the stock image
  * uid/gid/mode   vs the metadata taken from the stock image
  * file contents  vs the stock tree (or the arm64 staging tree)
"""
import hashlib, os, stat, sys

MNT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/newmnt'
STOCK = '/home/randyyy/x6532c-work/stockimg/vendorstock'
STAGE = '/home/randyyy/x6532c-work/hybrid'
WORK = '/home/randyyy/x6532c-work/hybridimg'

meta = {}
for line in open(os.path.join(WORK, 'meta.tsv')):
    p, uid, gid, mode = line.rstrip('\n').split('\t')
    meta[p] = (int(uid), int(gid), int(mode, 8))

labels = {}
for line in open(os.path.join(WORK, 'labels_map.txt')):
    p, ctx = line.rstrip('\n').split(' ', 1)
    labels[p] = ctx

def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

bad_lbl = bad_meta = bad_hash = 0
seen = set()
nfiles = nlinks = 0

for dirpath, dirnames, filenames in os.walk(MNT):
    rel = os.path.relpath(dirpath, MNT)
    base = '' if rel == '.' else rel
    for name in dirnames + filenames:
        full = os.path.join(dirpath, name)
        relp = os.path.join(base, name) if base else name
        seen.add(relp)

        st = os.lstat(full)
        want = meta.get(relp)
        if want is None:
            print('TIDAK ADA DI META:', relp)
            bad_meta += 1
        else:
            got = (st.st_uid, st.st_gid, stat.S_IMODE(st.st_mode))
            if got != want:
                print('META BEDA:', relp, 'img=', got, 'harap=', want)
                bad_meta += 1

        try:
            lbl = os.getxattr(full, 'security.selinux', follow_symlinks=False)
            lbl = lbl.rstrip(b'\x00').decode()
        except OSError as e:
            lbl = None
            print('LABEL HILANG:', relp, e)
        exp = labels.get('/vendor/' + relp)
        if lbl != exp:
            print('LABEL BEDA:', relp, 'img=', lbl, 'harap=', exp)
            bad_lbl += 1

        if stat.S_ISLNK(st.st_mode):
            nlinks += 1
            continue
        if stat.S_ISREG(st.st_mode):
            nfiles += 1
            src = os.path.join(STOCK, relp)
            if not os.path.exists(src):
                src = os.path.join(STAGE, relp)
            if not os.path.exists(src):
                print('SUMBER TIDAK ADA:', relp)
                bad_hash += 1
                continue
            if os.path.getsize(src) != st.st_size or sha1(src) != sha1(full):
                print('ISI BEDA:', relp, os.path.getsize(src), st.st_size)
                bad_hash += 1

missing = set(meta) - seen
for m in sorted(missing):
    print('HILANG DARI IMAGE:', m)

print('---')
print('file:', nfiles, 'symlink:', nlinks, 'total entri:', len(seen))
print('meta salah:', bad_meta, 'label salah:', bad_lbl, 'isi salah:', bad_hash,
      'hilang:', len(missing))
sys.exit(1 if (bad_meta or bad_lbl or bad_hash or missing) else 0)