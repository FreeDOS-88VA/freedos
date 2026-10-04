#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Independently inspect disposable guest-written M20 workflow checkpoints.

This is a separate, explicitly invoked QA inspector, NOT a make m20-disk input.
Private guest paths, hashes and numeric observations belong only in the requested
private output. Settled snapshots do not measure instantaneous in-program peak.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools/m20'))
from media import derive_layout, inspect, parse_d88

COPY_NAMES = {'HELLO.ASM', 'MZDEMO.ASM', 'BUILD.BAT'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_stages(stages, cluster_budget, minimum_free):
    """Take (report, file bytes) pairs in source/copy/edit/build order."""
    if len(stages) != 4 or cluster_budget < 1 or minimum_free < cluster_budget:
        raise ValueError('invalid workspace stages or capacity policy')
    base_report, base_files = stages[0]
    if not COPY_NAMES.issubset(base_files) or not base_report['fat_copies_equal']:
        raise ValueError('normal source disk or FAT is incomplete')
    original = base_report['files']
    baseline_free = len(base_report['free_clusters'])
    measurements = []
    for step, (report, files) in zip(('normal', 'copy', 'edit', 'build'), stages):
        if not report['fat_copies_equal'] or baseline_free < len(report['free_clusters']):
            raise ValueError(step + ': invalid FAT or free-cluster count')
        if {name: files[name] for name in original if name in files} != base_files or set(files) & set(original) != set(original):
            raise ValueError(step + ': distribution root file changed or disappeared')
        if set(files) - set(original) != {name for name in files if name.startswith('WORK/')}:
            raise ValueError(step + ': unrelated guest file or release root mutation')
        workspace = {name for name in files if name.startswith('WORK/')}
        if step in ('edit', 'build'):
            expected = {'WORK/' + name for name in COPY_NAMES} | {'WORK/HELLO.BAK'}
            if step == 'build':
                expected |= {'WORK/HELLO.COM', 'WORK/MZDEMO.EXE'}
            if not expected.issubset(workspace) or workspace - expected - {'WORK/PRE.TXT'}:
                raise ValueError(step + ': missing or unexpected work file')
        if step != 'normal':
            if 'WORK' not in report['directories']:
                raise ValueError(step + ': work directory missing')
            for name in COPY_NAMES - {'HELLO.ASM'}:
                if files.get('WORK/' + name) != base_files[name]:
                    raise ValueError(step + ': source copy changed')
            if step == 'copy' and (workspace != {'WORK/' + n for n in COPY_NAMES} or
                                   files['WORK/HELLO.ASM'] != base_files['HELLO.ASM']):
                raise ValueError('copy checkpoint is not the original source set')
            if step in ('edit', 'build') and (files.get('WORK/HELLO.BAK') != base_files['HELLO.ASM'] or
                    files.get('WORK/HELLO.ASM') == base_files['HELLO.ASM']):
                raise ValueError(step + ': editor did not save changed source and intact backup')
        if step == 'build':
            com = files.get('WORK/HELLO.COM', b'')
            mz = files.get('WORK/MZDEMO.EXE', b'')
            if len(com) < 5 or com[:1] == b'\0' or len(mz) < 28 or mz[:2] != b'MZ':
                raise ValueError('build checkpoint lacks both generated DOS programs')
            relocations = struct.unpack_from('<H', mz, 6)[0]
            if relocations < 1:
                raise ValueError('sample MZ lacks a relocation')
        delta = baseline_free - len(report['free_clusters'])
        if delta > cluster_budget or len(report['free_clusters']) < minimum_free - cluster_budget:
            raise ValueError(step + ': working-space reserve exhausted')
        measurements.append({'stage': step, 'additional_allocated_clusters': delta,
                             'free_clusters': len(report['free_clusters']),
                             'workspace_files': {name: {'bytes': len(files[name]),
                                        'clusters': len(report['files'][name]['clusters']),
                                        'sha256': digest(files[name])}
                                                 for name in sorted(workspace)}})
    return measurements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('normal', 'copy', 'edit', 'build'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == ROOT or ROOT in destination.parents:
        raise ValueError('private guest evidence output must be outside the public repository')
    if args.output.exists():
        raise ValueError('refusing to overwrite workspace evidence')
    images = [getattr(args, name).read_bytes() for name in ('normal', 'copy', 'edit', 'build')]
    manifest = json.loads(args.manifest.read_text())
    if digest(images[0]) != manifest['distribution_d88']['sha256'] or len(images[0]) != manifest['distribution_d88']['size_bytes']:
        raise ValueError('normal disk differs from the exact source build manifest')
    spec = json.loads((ROOT / 'config/m20/media.json').read_text())
    budget = json.loads((ROOT / 'config/m20/workspace-budget.json').read_text())
    layout = derive_layout(spec)
    sectors = [parse_d88(image, spec, layout)[1][:spec['geometry']['bytes_per_sector']]
               for image in images]
    if any(sector != sectors[0] for sector in sectors[1:]):
        raise ValueError('guest checkpoint modified the native boot sector')
    reports = [inspect(image, spec) for image in images]
    rows = check_stages(reports, budget['sample_workflow']['workspace_cluster_budget'],
                        budget['minimum_free_clusters_after_build'])
    record = {'scope': 'private guest readback; settled checkpoint snapshots, not an instantaneous IO peak',
              'normal_d88_sha256': digest(images[0]),
              'guest_checkpoint_sha256': {name: digest(image) for name, image in zip(('copy', 'edit', 'build'), images[1:])},
              'source_parent_revision': manifest['parent_revision'],
              'budget_clusters': budget['sample_workflow']['workspace_cluster_budget'],
              'measurements': rows, 'highest_observed_additional_clusters': max(r['additional_allocated_clusters'] for r in rows),
              'guest_execution': 'MUST be checked independently; filesystem contents alone do not prove execution'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2) + '\n')
    print('Workspace stage readback PASS; evidence written to requested private output')


if __name__ == '__main__':
    main()
