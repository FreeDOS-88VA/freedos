#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Executed only in a fresh offline Linux/amd64 toolchain container.
set -euo pipefail
test "$(uname -m)" = x86_64
test "$(dpkg --print-architecture)" = amd64
export PATH=/opt/openwatcom-1.9/binl:$PATH
export WATCOM=/opt/openwatcom-1.9 INCLUDE=/opt/openwatcom-1.9/h
export LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH=1787814827 PYTHONDONTWRITEBYTECODE=1
umask 022
mkdir -p /work/source /work/result
tar -xf /input/parent.tar -C /work/source
for name in fdkernel freecom country; do
    mkdir -p "/work/source/components/$name"
    tar -xf "/input/$name.tar" -C "/work/source/components/$name"
done
cd /work/source
python3 tools/m16/verify_isolation.py
mkdir -p /work/pydeps
python3 -m zipfile -e /input/unicorn-*.whl /work/pydeps
export PYTHONPATH=/work/pydeps
python3 - <<'PY'
import hashlib,json
from pathlib import Path
lock=json.loads(Path('manifests/toolchains.lock.json').read_text())
for item in lock['canonical']['open_watcom']['host_tools']:
    data=(Path('/opt/openwatcom-1.9')/item['path']).read_bytes()
    assert len(data)==item['size'] and hashlib.sha256(data).hexdigest()==item['sha256']
PY
cd components/fdkernel/pc88va
wmake -ms -h -f makefile.m13.wc clean all
cp bin/KERNEL.SYS /work/result/kernel-linked.exe
cp build/KVA8616.map /work/result/kernel.map
python3 - <<'PY'
import os,re
from datetime import datetime,timezone
from pathlib import Path
p=Path('/work/result/kernel.map')
stamp=datetime.fromtimestamp(int(os.environ['SOURCE_DATE_EPOCH']),timezone.utc).strftime('%y/%m/%d %H:%M:%S')
text,count=re.subn(r'^Created on:.*$', 'Created on:       '+stamp, p.read_text(), flags=re.MULTILINE)
assert count==1
text,count=re.subn(r'^Link time:.*$', 'Link time: 00:00.00', text, flags=re.MULTILINE)
assert count==1
p.write_text(text)
PY
cd ../sys
wmake -ms -h -f makefile.pc88va clean all
cp sysva.exe /work/result/SYSVA.EXE
cd /work/source/components/freecom
python3 - <<'PY'
import json
from pathlib import Path
stamp=json.loads(Path('/work/source/config/m16/freecom-build-timestamp.json').read_text())
source=Path('config.std').read_text()
line='CFLAGS2 = -DFREECOM_BUILD_DATE=\\"'+stamp['formatted_date']+'\\" -DFREECOM_BUILD_TIME=\\"'+stamp['formatted_time']+'\\"\n'
assert source.count('$(CFG):')==1
Path('config.mak').write_text(source.replace('$(CFG):',line+'$(CFG):',1))
PY
gcc utilsc/critstrs.c -o utilsc/critstrs.exe
bash build.sh pc88va no-xms-swap wc english
cp command.com /work/result/COMMAND.COM
cd /work/source/components/country
nasm -f bin country.asm -o /work/result/COUNTRY.SYS
cd /work/source
nasm -f bin tests/m16/system_com_probe.asm -o /work/result/COMPROBE.COM
nasm -f bin tests/m16/dos_input_probe.asm -o /work/result/DOSINPUT.COM
nasm -f bin tests/m16/dos_repeat_probe.asm -o /work/result/DOSREPT.COM
nasm -f obj tests/m16/system_mz_probe.asm -o /work/result/mz_probe.obj
wlink system dos option quiet name /work/result/MZPROBE.EXE file /work/result/mz_probe.obj
python3 tools/m16/finish_image.py --output /work/result
mkdir -p build
python3 tools/m16/verify_m13_linked_placement.py --kernel /work/result/kernel-linked.exe --map /work/result/kernel.map --carrier /work/result/KERNEL.SYS --placement /work/result/carrier.json
if [ "${M16_BUILD_PASS:-1}" = 1 ]; then
python3 -B -m unittest discover -s tests/m16 -p 'test_m13_memory_placement.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_m13_carrier_tail.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_floppy_media.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_loader_builder.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_loadseg_contract.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_freecom_input_source.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_dos_input_probe.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_dos_freecom_editor.py'
python3 -B -m unittest discover -s tests/m16 -p 'test_dos_repeat_probe.py'
fi
