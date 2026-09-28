#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Prepare the pinned public toolchain without a historical milestone runner."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


def verify_image(image, lock):
    info = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image]))[0]
    if (info['Os'], info['Architecture']) != ('linux', 'amd64'):
        raise ValueError('Toolchain image must be Linux/amd64')
    program = '''import hashlib,json,pathlib,sys
for item in json.loads(sys.stdin.read()):
 data=(pathlib.Path('/opt/openwatcom-1.9')/item['path']).read_bytes()
 assert len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256']
'''
    subprocess.run(['docker', 'run', '--rm', '-i', '--platform', 'linux/amd64',
                    '--network', 'none', '--entrypoint', 'python3', info['Id'], '-c', program],
                   input=json.dumps(lock['open_watcom']['host_tools']).encode(), check=True)
    return info['Id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='freedos-pc88va-m16:local',
                        help='Pinned Linux/amd64 image used for the M16 source build')
    parser.add_argument('--rebuild', action='store_true')
    args = parser.parse_args()
    lock = json.loads((ROOT / 'manifests/toolchains.lock.json').read_text())['canonical']
    exists = subprocess.run(['docker', 'image', 'inspect', args.image],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if exists and not args.rebuild:
        print('Verified existing toolchain:', verify_image(args.image, lock))
        return
    cache = ROOT / 'build/m16-toolchain-download'
    cache.mkdir(parents=True, exist_ok=True)
    ow = lock['open_watcom']
    archive = cache / ow['package']
    if not archive.exists():
        partial = archive.with_suffix('.part')
        with urllib.request.urlopen(ow['official_github_url']) as response, partial.open('wb') as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        partial.rename(archive)
    data = archive.read_bytes()
    if len(data) != ow['asset_size'] or hashlib.sha256(data).hexdigest() != ow['sha256']:
        raise ValueError('Open Watcom archive identity mismatch')
    dockerfile = ROOT / 'tools/m16/toolchain/Dockerfile'
    if lock['base_image']['amd64_manifest_digest'] not in dockerfile.read_text():
        raise ValueError('Dockerfile base differs from toolchain lock')
    subprocess.run(['docker', 'buildx', 'build', '--load', '--platform', 'linux/amd64',
                    '--build-context', 'watcom=' + str(cache),
                    '--build-arg', 'APT_SNAPSHOT=' + lock['apt']['snapshot_id'],
                    '--build-arg', 'OW_PACKAGE_SIZE=' + str(ow['asset_size']),
                    '--build-arg', 'OW_PUBLISHER_MD5=' + ow['publisher_md5'],
                    '--build-arg', 'OW_PACKAGE_SHA256=' + ow['sha256'],
                    '-t', args.image, str(dockerfile.parent)], check=True)
    print('Verified built toolchain:', verify_image(args.image, lock))


if __name__ == '__main__':
    main()
