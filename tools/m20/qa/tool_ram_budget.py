#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Source-bound DOS MZ EXEC lower bounds, not runtime heap peaks or installed RAM minima."""
import hashlib
import struct

TOOLS = ('EDLIN.EXE', 'MORE.EXE', 'CHKDSK.EXE', 'FORMAT.EXE',
         'SYS.EXE', 'MEM.EXE', 'JWASMR.EXE')


def mz_exec_floor(data):
    if len(data) < 28:
        raise ValueError('MZ header is truncated')
    (magic, last, pages, relocations, header, minimum, maximum, ss, sp,
     _checksum, ip, cs, reloc_offset, overlay) = struct.unpack_from('<14H', data)
    if magic != 0x5a4d or not pages or last > 511 or overlay:
        raise ValueError('DOS MZ signature, pages, or overlay differs')
    declared = (pages-1)*512 + (last if last else 512)
    if (declared != len(data) or header*16 < 28 or header*16 > declared or
            reloc_offset + relocations*4 > header*16):
        raise ValueError('MZ file or relocation table is outside its header')
    # The pinned FreeDOS DosExeLoader uses exPages*32-exHeaderSize paragraphs,
    # not ceil((actual MZ file length-header bytes)/16). Thus a partial final
    # file page still occupies a whole 512-byte loader page at EXEC.
    loaded_paras = pages*32 - header
    actual_image = declared - header*16
    real_paras = (actual_image + 15)//16
    psp_block_paras = 16 + loaded_paras + minimum
    if (loaded_paras < 0 or psp_block_paras > 65535 or
            16*ss + sp > 16*(loaded_paras + minimum) or
            16*cs + ip >= 16*(loaded_paras + minimum)):
        raise ValueError('MZ required PSP block, stack or entry exceeds its declared allocation')
    return {'source_file_sha256': hashlib.sha256(data).hexdigest(),
            'source_file_bytes': len(data), 'mz_real_image_bytes': actual_image,
            'mz_real_image_paragraphs': real_paras,
            'dos_loader_rounded_image_paragraphs': loaded_paras,
            'page_rounding_extra_paragraphs': loaded_paras-real_paras,
            'mz_minalloc_paragraphs': minimum, 'mz_maxalloc_paragraphs': maximum,
            'minimum_psp_block_paragraphs': psp_block_paras,
            'minimum_psp_block_bytes': psp_block_paras*16,
            'separate_mcb_header_bytes': 16,
            'scope': 'MZ EXEC entry lower bound only; environment, disk buffers, source/heap growth and instantaneous peaks are excluded'}


def all_tool_floors(files):
    if any(name not in files for name in TOOLS):
        raise ValueError('normal media lacks a mandatory M20 DOS application')
    return {name: mz_exec_floor(files[name]) for name in TOOLS}
