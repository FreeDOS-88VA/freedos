#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Run only in a fresh, network-disabled Linux/amd64 toolchain container.
set -euo pipefail
test "$(uname -m)" = x86_64
test "$(dpkg --print-architecture)" = amd64
export PATH=/opt/openwatcom-1.9/binl:$PATH
export WATCOM=/opt/openwatcom-1.9 INCLUDE=/opt/openwatcom-1.9/h
export LIB='/opt/openwatcom-1.9/lib286;/opt/openwatcom-1.9/lib286/dos'
: "${M20_PARENT_SHA:?M20_PARENT_SHA must be supplied by the host source lock}"
: "${M20_TOOLCHAIN_IDENTITY:?M20_TOOLCHAIN_IDENTITY must be supplied by the host toolchain check}"
: "${M20_SOURCE_DATE_EPOCH:?M20_SOURCE_DATE_EPOCH must be supplied by the host manifest}"
export LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$M20_SOURCE_DATE_EPOCH" PYTHONDONTWRITEBYTECODE=1
umask 022
mkdir -p /work/source /work/result /work/pydeps
tar -xf /input/parent.tar -C /work/source
for name in fdkernel freecom country edlin jwasm; do
    mkdir -p "/work/source/components/$name"
    tar -xf "/input/$name.tar" -C "/work/source/components/$name"
done
cd /work/source
python3 -B tools/m20/verify_isolation.py
python3 -B tools/m20/verify_source_audit.py
wheel_count=0
for wheel in /input/*.whl; do
    python3 -m zipfile -e "$wheel" /work/pydeps
    wheel_count=$((wheel_count + 1))
done
test "$wheel_count" -eq 1
export PYTHONPATH=/work/pydeps
python3 - <<'PY'
import json
from importlib.metadata import version
from pathlib import Path
spec=json.loads(Path('config/m20/host-tooling.json').read_text())['unicorn_wheel']
assert version(spec['package']) == spec['version']
import unicorn
assert unicorn.__version__ == spec['version']
PY
python3 - <<'PY'
import hashlib,json
from pathlib import Path
lock=json.loads(Path('manifests/toolchains.lock.json').read_text())
for item in lock['canonical']['open_watcom']['host_tools']:
    data=(Path('/opt/openwatcom-1.9')/item['path']).read_bytes()
    assert len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256'], item['name']
PY
cd components/fdkernel/pc88va
wmake -ms -h -f makefile.m13.wc 'CC=python3 /work/source/tools/m20/kernel_cc.py' clean all
cd ../sys
wmake -ms -h -f makefile.pc88va clean all
cd /work/source/components/freecom
python3 - <<'PY'
import json
from pathlib import Path
stamp=json.loads(Path('/work/source/config/m20/freecom-build-timestamp.json').read_text())
source=Path('config.std').read_text()
line='CFLAGS2 = -DFREECOM_BUILD_DATE=\\"'+stamp['formatted_date']+'\\" -DFREECOM_BUILD_TIME=\\"'+stamp['formatted_time']+'\\"\n'
assert source.count('$(CFG):')==1
Path('config.mak').write_text(source.replace('$(CFG):',line+'$(CFG):',1))
PY
gcc utilsc/critstrs.c -o utilsc/critstrs.exe
bash build.sh pc88va no-xms-swap wc english
# FreeCOM's own build patches a 6 KiB heap. The VA build has no XMS swap, so
# every heap byte stays resident; ptchsize estimates its minimum at about
# 1.8 KiB. Use FreeCOM's own tool to set 3 KiB.
utils/ptchsize.exe command.com +3KB
cd /work/source
python3 -B tools/m20/finish_image.py /work/result
python3 -B tools/m20/verify_m13_linked_placement.py \
    --kernel /work/result/kernel-linked.exe \
    --map /work/result/kernel.map \
    --carrier /work/result/KERNEL.SYS \
    --placement /work/result/carrier.json
python3 -B -m unittest discover -s tests/m20 -p 'test_*.py' -v
