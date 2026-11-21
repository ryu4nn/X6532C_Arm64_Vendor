#!/usr/bin/env python3
"""Walk an extracted erofs tree and record the authoritative uid/gid/mode
of every entry by querying dump.erofs --path on the source image."""
import os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

IMG = sys.argv[1] if len(sys.argv) > 1 else 'vendor_a.img'
ROOT = sys.argv[2] if len(sys.argv) > 2 else 'vendorstock'
OUT = sys.argv[3] if len(sys.argv) > 3 else 'fsmeta.tsv'
DUMP = '/home/randyyy/x6532c-work/tools/bin/dump.erofs'

rx = re.compile(r'Uid:\s*(\d+)\s+Gid:\s*(\d+)\s+Access:\s*(\d+)/(\S+)')

paths = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    base = '' if rel == '.' else rel
    for d in dirnames:
        paths.append(os.path.join(base, d))
    for f in filenames:
        paths.append(os.path.join(base, f))

def probe(rel):
    p = '/' + rel
    r = subprocess.run([DUMP, '--path=' + p, IMG], capture_output=True, text=True)
    m = rx.search(r.stdout)
    if not m:
        return (rel, None, None, None)
    return (rel, int(m.group(1)), int(m.group(2)), int(m.group(3), 8))

with ThreadPoolExecutor(max_workers=12) as ex:
    res = list(ex.map(probe, paths))

bad = [r for r in res if r[1] is None]
with open(OUT, 'w') as f:
    for rel, uid, gid, mode in res:
        if uid is None:
            continue
        f.write('%s\t%d\t%d\t%04o\n' % (rel, uid, gid, mode))

print('entri:', len(res), 'gagal:', len(bad), 'ditulis:', len(res) - len(bad))
for b in bad[:10]:
    print('  GAGAL', b[0])