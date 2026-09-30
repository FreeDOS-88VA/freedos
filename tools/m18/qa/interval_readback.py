#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reconcile public linked placement with one private DOS MCB snapshot.

Separate QA-only operation: private console output never enters make m18-disk.
Physical ownership outside the DOS arena cannot be inferred from MCBs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m18'))
from media import inspect

ROW = re.compile(r'^MCB ([0-9A-F]{4}) ([MZ]) owner=([0-9A-F]{4}) (\S+)\s+name=.*? payload=([0-9A-F]+)-([0-9A-F]+) bytes=(\d+) paras=(\d+)\r?$', re.M)
RANGE = re.compile(r'Managed MCB range: ([0-9A-F]+)-([0-9A-F]+) bytes \(end exclusive\)')
SUMMARY = re.compile(r'Blocks: (\d+); managed bytes: (\d+); MCB overhead: (\d+)')
PAYLOAD = re.compile(r'Free payload: (\d+) bytes; largest free block: (\d+) bytes')
ALLOC = re.compile(r'Allocated payload: (\d+) bytes; system-owned: (\d+) bytes')
OWN = re.compile(r'MEMMAP-owned payload \(PSP ([0-9A-F]{4}), including owned environment\): (\d+) bytes')


def parse_guest(text, carrier, installed_kib):
    if not 256 <= installed_kib <= 640 or installed_kib % 128:
        raise ValueError('unsupported capacity for the declared native profile')
    for pattern in (RANGE, SUMMARY, PAYLOAD, ALLOC, OWN):
        if len(pattern.findall(text)) != 1:
            raise ValueError('missing or repeated MCB accounting field')
    if text.count('MCB chain: VALID') != 1:
        raise ValueError('guest MCB chain not reported valid exactly once')
    low, end = (int(value, 16) for value in RANGE.search(text).groups())
    count, managed, overhead = (int(v) for v in SUMMARY.search(text).groups())
    free, largest = (int(v) for v in PAYLOAD.search(text).groups())
    allocated, system = (int(v) for v in ALLOC.search(text).groups())
    own_psp, own = OWN.search(text).groups()
    psp, own = int(own_psp, 16), int(own)
    resident = carrier['split']['resident_text']
    base = carrier['layout']['entry']
    top = installed_kib * 1024
    if (not all(isinstance(n, int) for n in resident) or len(resident) != 2 or
            base >= resident[0] or resident[0] >= resident[1] or
            resident[1] != low or end != top or top - low != managed):
        raise ValueError('MCB arena does not meet the exact linked-resident and installed-RAM boundary')
    rows = []
    for groups in ROW.findall(text):
        seg, kind, owner, label, payload_start, payload_end, size, paragraphs = groups
        s, ownseg = int(seg, 16), int(owner, 16)
        start, finish = int(payload_start, 16), int(payload_end, 16)
        length, paras = int(size), int(paragraphs)
        if (start != (s + 1) * 16 or finish != start + length or length != paras * 16 or
                (ownseg == 0 and label != 'FREE') or (ownseg == 8 and label != 'SYSTEM')):
            raise ValueError('MCB header, owner class or exclusive endpoint disagrees')
        rows.append({'mcb_start': s * 16, 'payload_start': start, 'end': finish,
                     'bytes': length, 'owner_psp': ownseg, 'type': kind})
    if len(rows) != len(re.findall(r'^MCB (?!chain: ).*$', text, re.M)) or len(rows) != count or overhead != count * 16 or not rows or rows[0]['mcb_start'] != low or rows[-1]['type'] != 'Z':
        raise ValueError('MCB header count, first or terminal type differs')
    if rows[0]['owner_psp'] != 8 or rows[0]['type'] != 'M':
        raise ValueError('first linked resident MCB does not own permanent kernel work')
    for before, after in zip(rows, rows[1:]):
        if before['type'] != 'M' or before['end'] != after['mcb_start']:
            raise ValueError('MCB chain has a hole, overlap or early terminator')
    if rows[-1]['end'] != end:
        raise ValueError('terminal MCB does not reach measured RAM top')
    actual_free = sum(r['bytes'] for r in rows if r['owner_psp'] == 0)
    actual_allocated = sum(r['bytes'] for r in rows if r['owner_psp'] != 0)
    actual_system = sum(r['bytes'] for r in rows if r['owner_psp'] == 8)
    actual_own = sum(r['bytes'] for r in rows if r['owner_psp'] == psp)
    if (actual_free, actual_allocated, actual_system, actual_own) != (free, allocated, system, own):
        raise ValueError('MCB sums or observer ownership disagree')
    if max((r['bytes'] for r in rows if r['owner_psp'] == 0), default=0) != largest or free + allocated + overhead != managed:
        raise ValueError('largest free block or total arena arithmetic disagrees')
    for owner in {r['owner_psp'] for r in rows} - {0, 8}:
        candidates = [r for r in rows if r['payload_start'] == owner * 16 and r['owner_psp'] == owner]
        if len(candidates) != 1 or candidates[0]['bytes'] < 256:
            raise ValueError('owner PSP lacks its live MCB or a complete PSP')
    reference = carrier['minimum_runtime_memory_kb'] * 1024
    if installed_kib < carrier['minimum_runtime_memory_kb']:
        raise ValueError('carrier is not supported at the installed capacity')
    ranges = carrier['layout']['ranges']
    scratch, ring, bridge, bridge_stack = (ranges[name] for name in
                                            ('scratch', 'ring', 'bridge', 'bridge_stack'))
    init, init_stack = carrier['split']['init'], carrier['split']['init_stack']
    if (len({len(v) for v in (scratch, ring, bridge, bridge_stack, init, init_stack)}) != 1 or
            scratch != [reference-0x9000, reference-0x8000] or
            ring != [reference-0x8000, reference-0x7000] or
            bridge != [reference-0x19000, reference-0x18000] or
            bridge_stack != [reference-0x1010, reference-0x10] or
            init_stack != [reference-0x3000, reference-0x2000] or
            init[1] > init_stack[0] or init[0] < ring[1] or
            bridge[0] + carrier['size'] > scratch[0] or
            carrier['layout']['ranges']['image'][0] != base or
            low > carrier['layout']['ranges']['image'][1]):
        raise ValueError('linked carrier, scratch, ring or translated INIT placement disagrees')
    offset = top - reference
    def translate(pair):
        return {'start': pair[0] + offset, 'end': pair[1] + offset,
                'bytes': pair[1]-pair[0], 'lifetime': 'boot only; retired before shell'}
    return {'installed_bytes': top, 'policy_excluded_bytes': base,
            'temporary_at_boot': {name: translate(pair) for name, pair in
                                  (('carrier_bridge', bridge), ('scratch', scratch),
                                   ('ring', ring), ('init', init),
                                   ('init_stack', init_stack), ('bridge_stack', bridge_stack))},
            'linked_resident_low': {'start': base, 'end': low, 'bytes': low-base},
            'kernel_work': {'start': low, 'end': rows[0]['end'],
                            'owned_payload_bytes': rows[0]['bytes'], 'owned_header_bytes': 16},
            'arena': {'start': low, 'end': top, 'bytes': managed, 'headers': overhead,
                      'allocated_payload_bytes': allocated, 'system_payload_bytes': system,
                      'free_payload_bytes': free, 'largest_raw_free_payload_bytes': largest,
                      'observer_payload_bytes': own, 'observer_psp': psp},
            'owner_count': len({r['owner_psp'] for r in rows} - {0, 8}),
            'mcb_count': count, 'mcbs': rows,
            'outside_arena': 'physical/firmware/VRAM ownership NOT established by DOS MCB traversal'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--normal', type=Path, required=True)
    parser.add_argument('--carrier', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--installed-kib', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dest = args.output.resolve()
    if dest == ROOT or ROOT in dest.parents or args.output.exists():
        raise ValueError('private MCB evidence must be new and outside the public source tree')
    manifest = json.loads(args.manifest.read_text())
    image = args.normal.read_bytes()
    if (hashlib.sha256(image).hexdigest() != manifest['distribution_d88']['sha256'] or
            len(image) != manifest['distribution_d88']['size_bytes']):
        raise ValueError('normal image does not match the public source manifest')
    spec = json.loads((ROOT / 'config/m18/media.json').read_text())
    _, files = inspect(image, spec)
    carrier = json.loads(args.carrier.read_text())
    if hashlib.sha256(files['KERNEL.SYS']).hexdigest() != carrier['sha256']:
        raise ValueError('carrier does not match the source disk')
    record = parse_guest(args.snapshot.read_text(encoding='ascii'), carrier, args.installed_kib)
    record['parent_revision'] = manifest['parent_revision']
    record['normal_sha256'] = manifest['distribution_d88']['sha256']
    record['snapshot_sha256'] = hashlib.sha256(args.snapshot.read_bytes()).hexdigest()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open('x') as output:
        json.dump(record, output, indent=2)
        output.write('\n')
    print('Linked resident, guest MCB accounting and measured RAM top reconcile; private output recorded')


if __name__ == '__main__':
    main()
