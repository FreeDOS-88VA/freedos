#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Bind the reviewed storage/configuration sources to the exported kernel pin."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[2]

def verify(root):
    audit=json.loads((root/'config/m17/source-audit.json').read_text())
    lock=json.loads((root/'manifests/m17-components.lock.json').read_text())
    if set(audit)!={'schema_version','kernel_commit','files'} or audit['schema_version']!=1:
        raise ValueError('Source audit schema')
    kernel=next(c for c in lock['components'] if c['name']=='fdkernel')
    if audit['kernel_commit']!=kernel['commit']:
        raise ValueError('Source audit kernel drift')
    required={'kernel/config.c','kernel/main.c','kernel/initdisk.c','kernel/execrh.asm',
              'kernel/intr.asm','kernel/init-mod.h','kernel/blockio.c','kernel/fatfs.c',
              'hdr/device.h','hdr/fat.h','pc88va/makefile.m13.wc','pc88va/kernel/m13_platform.asm'}
    if set(audit['files'])!=required:
        raise ValueError('Missing/unknown source audit input')
    for path,digest in audit['files'].items():
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('Malformed source digest')
        if hashlib.sha256((root/'components/fdkernel'/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Reviewed source drift: '+path)
    print('M17 reviewed sources match pinned kernel')

if __name__=='__main__':verify(ROOT)
