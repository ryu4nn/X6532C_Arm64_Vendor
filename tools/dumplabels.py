#!/usr/bin/env python3
"""Dump authoritative SELinux labels (and check for capabilities) from a
mounted erofs image, using os.getxattr directly."""
import os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/opencode/erofsmnt'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'labels.tsv'

rows = []
missing = []
caps = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    base = '' if rel == '.' else rel
    for name in dirnames + filenames:
        full = os.path.join(dirpath, name)
        relp = os.path.join(base, name) if base else name
        try:
            lbl = os.getxattr(full, 'security.selinux', follow_symlinks=False)
        except OSError:
            missing.append(relp)
            lbl = None
        if lbl is not None:
            rows.append((relp, lbl.rstrip(b'\x00').decode()))
        try:
            if 'security.capability' in os.listxattr(full, follow_symlinks=False):
                caps.append(relp)
        except OSError:
            pass

with open(OUT, 'w') as f:
    for p, l in rows:
        f.write('%s\t%s\n' % (p, l))

from collections import Counter
print('entri berlabel:', len(rows), 'tanpa label:', len(missing), 'ber-caps:', len(caps))
for k, v in Counter(l for _, l in rows).most_common():
    print('  %-40s %d' % (k, v))
for m in missing[:10]:
    print('  TANPA LABEL', m)
for c in caps[:10]:
    print('  CAPS', c)