#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""M20-maintained ROM-free checks for linked kernel placement and console ABI.

Copied from the integrated M17 implementation at M18 START_SHA
`d81bba18f0e4793d7165fb0acfdf7e229e160c83`; M20 owns this copy and does not
inherit prior milestone test results.
"""
import argparse
import json
from pathlib import Path
import re
import struct

from build_compressed_kernel import parse_mz, split_image


def symbols(path):
    result = {}
    for line in path.read_text().splitlines():
        match = re.match(r'^([0-9a-fA-F]{4}):([0-9a-fA-F]{4})[*+s]*\s+(\S+)$', line)
        if match:
            seg, off, name = match.groups()
            value = (int(seg, 16), int(off, 16))
            if name in result and result[name] != value:
                raise ValueError('ambiguous linked symbol: ' + name)
            result[name] = value
    return result


def verify_init_ownership(syms, init_source, load):
    """Check lifetimes by linear address, not by segment spelling alone."""
    start, end = init_source
    if not 0 <= start < end < 0x100000:
        raise ValueError('invalid linked INIT interval')
    disposable = ('DynAlloc_', 'DynFree_', 'DynLast_', 'dsk_init_',
                  '_pc88va_print_model', '_init_stacks', 'INIT_CALL_INTR',
                  'INIT_PSPSET', 'SET_DTA', '_query_cpu', '_query_memdisk',
                  'UMB_GET_LARGEST')
    resident = ('_P_0', 'init_fatal_', 'pc88va_release_boot_memory_')
    for name in disposable + resident:
        if name not in syms:
            raise ValueError('missing lifetime symbol: ' + name)
        segment, offset = syms[name]
        address = (segment + load) * 16 + offset
        inside = start <= address < end
        if inside != (name in disposable):
            raise ValueError('incorrect linked lifetime: ' + name)


def verify(kernel, link_map):
    from unicorn import (Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE,
                         UC_HOOK_INSN, UC_HOOK_INTR)
    from unicorn import x86_const as r
    syms = symbols(link_map)
    members = ['pc88va_dos_getc_', 'pc88va_console_read_dos_',
               'pc88va_console_peek_dos_', 'pc88va_m11_character_',
               'pc88va_m16_input_flush_', 'pc88va_m16_count_',
               'pc88va_m10_state_', 'ConRead', 'CommonNdRdExit']
    frames = {syms[name][0] for name in members}
    if len(frames) != 1:
        raise ValueError('near platform references use different linked code frames')
    if syms['_ReqPktPtr'][0] in frames:
        raise ValueError('test requires the real independent dispatcher data frame')
    h, body, relocations = parse_mz(kernel.read_bytes())
    load = 0x1000
    split = None
    if b'M13PLAN1' in body:
        body, split = split_image(body, relocations, link_map, load)
        verify_init_ownership(syms, split['init_source'], load)
    body = bytearray(body)
    for off, seg in struct.iter_unpack('<HH', relocations):
        at = seg * 16 + off
        word = struct.unpack_from('<H', body, at)[0]
        struct.pack_into('<H', body, at, word + load)
    cpu = Uc(UC_ARCH_X86, UC_MODE_16)
    cpu.mem_map(0, 0x100000)
    cpu.mem_write(load * 16, bytes(body))
    if split:
        for source, destination in [('init_source', 'init'), ('hma_source', 'resident_text')]:
            start, end = split[source]
            cpu.mem_write(split[destination][0], bytes(cpu.mem_read(start, end - start)))
    def address(name):
        seg, off = syms[name]
        return (seg + load) * 16 + off
    def write_word(name, value):
        cpu.mem_write(address(name), struct.pack('<H', value))
    packet, destination, stack = 0x40000, 0x41000, 0x5000
    cpu.mem_write(address('_ReqPktPtr'), struct.pack('<HH', 0, packet // 16))
    cpu.mem_write(packet, bytes([26, 0, 5]) + bytes(23))
    cpu.mem_write(address('pc88va_m10_state_'), b'\x02')
    write_word('pc88va_m16_queue_', ord('v'))
    cpu.mem_write(address('pc88va_m16_count_'), b'\x01')
    cpu.hook_add(UC_HOOK_INSN, lambda uc, port, size, _: 0xff,
                 None, 1, 0, r.UC_X86_INS_IN)
    def platform_int(uc, interrupt, _):
        if interrupt != 0x80:
            return
        # The placement verifier exercises only the successful reset/read
        # contract.  Advance over the real-mode INT instruction and return
        # CF clear; no guest service is emulated here.
        # Unicorn reports IP after the two-byte INT instruction here; leave
        # it untouched so the following SBB/return conversion still runs.
        uc.reg_write(r.UC_X86_REG_EFLAGS,
                     uc.reg_read(r.UC_X86_REG_EFLAGS) & ~1)
    cpu.hook_add(UC_HOOK_INTR, platform_int)
    exits = {address(n): n for n in ['_IOExit', '_IODone', '_IOErrorExit']}
    stopped = []
    def boundary(uc, at, size, _):
        if at in exits:
            stopped.append(exits[at])
            uc.emu_stop()
    cpu.hook_add(UC_HOOK_CODE, boundary)
    def invoke(name, expected, count=0):
        stopped.clear()
        seg, off = syms[name]
        for reg, value in [(r.UC_X86_REG_CS, seg + load), (r.UC_X86_REG_IP, off),
                           (r.UC_X86_REG_DS, syms['DATASTART'][0] + load),
                           (r.UC_X86_REG_SS, stack), (r.UC_X86_REG_SP, 0x800),
                           (r.UC_X86_REG_ES, destination // 16),
                           (r.UC_X86_REG_DI, 0), (r.UC_X86_REG_CX, count),
                           (r.UC_X86_REG_EFLAGS, 0x202)]:
            cpu.reg_write(reg, value)
        cpu.emu_start(address(name), 0xfffff, count=20000)
        assert stopped == [expected], (name, stopped)
        assert cpu.reg_read(r.UC_X86_REG_SS) == stack
        assert cpu.reg_read(r.UC_X86_REG_SP) == 0x800
    for _ in range(2):
        invoke('CommonNdRdExit', '_IOExit')
        assert cpu.mem_read(packet + 13, 1) == b'v'
        assert cpu.mem_read(address('pc88va_m16_count_'), 1) == b'\x01'
    invoke('ConRead', '_IOExit', 1)
    assert cpu.mem_read(destination, 1) == b'v'
    assert cpu.mem_read(address('pc88va_m16_count_'), 1) == b'\x00'
    invoke('CommonNdRdExit', '_IODone')
    cpu.mem_write(address('pc88va_m16_count_'), b'\x01')
    invoke('ConInpFlush', '_IOExit')
    assert cpu.mem_read(address('pc88va_m16_count_'), 1) == b'\x00'
    for name, words in [('FL_RESET', 1), ('WRITEPCCLOCK', 2), ('WRITEATCLOCK', 4)]:
        seg, off = syms[name]
        caller = b''.join(b'\xb8' + struct.pack('<H', 0xA000 + i) + b'\x50'
                          for i in range(words))
        caller += b'\x9a' + struct.pack('<HH', off, seg + load)
        cpu.mem_write(0x60000, caller)
        saved = [(r.UC_X86_REG_BX, 0x1234), (r.UC_X86_REG_CX, 0x2345),
                 (r.UC_X86_REG_DX, 0x3456), (r.UC_X86_REG_SI, 0x4567),
                 (r.UC_X86_REG_DI, 0x5678), (r.UC_X86_REG_BP, 0x6789),
                 (r.UC_X86_REG_DS, 0x4000), (r.UC_X86_REG_ES, 0x4100),
                 (r.UC_X86_REG_SS, stack), (r.UC_X86_REG_SP, 0x800)]
        for reg, value in saved + [(r.UC_X86_REG_CS, 0x6000), (r.UC_X86_REG_IP, 0)]:
            cpu.reg_write(reg, value)
        cpu.emu_start(0x60000, 0x60000 + len(caller), count=100)
        assert cpu.reg_read(r.UC_X86_REG_CS) == 0x6000, name
        assert cpu.reg_read(r.UC_X86_REG_IP) == len(caller), name
        expected_ax = 1 if name == 'FL_RESET' else 0xA000 + words - 1
        assert cpu.reg_read(r.UC_X86_REG_AX) == expected_ax, (name, hex(cpu.reg_read(r.UC_X86_REG_AX)))
        for reg, value in saved:
            assert cpu.reg_read(reg) == value, name
    if split:
        root, temporary, ceiling = 0x3000, 0x8000, 0xA000
        frame = syms['_p_0_tos'][1] - 48  # reserve the real P_0 local/frame budget
        data_segment = syms['_first_mcb'][0] + load
        def mcb(segment, kind, owner, paragraphs):
            cpu.mem_write(segment * 16, struct.pack('<BHH', kind, owner, paragraphs) + bytes(11))
        def setup_release():
            write_word('_first_mcb', root)
            write_word('_pc88va_boot_mcb', temporary)
            write_word('_pc88va_boot_top', ceiling)
            write_word('_LoL_nbuffers', 20)
            write_word('_maxsecsize', 1024)
            cpu.mem_write(address('_firstbuf'), struct.pack('<HH', 16, root))
            cpu.mem_write(address('_CDSp'), struct.pack('<HH', 0, root + 0x600))
            cpu.mem_write(address('_lastdrive'), b'\x05')
            mcb(root, ord('M'), 0, temporary - root - 1)
            mcb(temporary, ord('Z'), 8, ceiling - temporary - 1)
        water = [frame]
        def measure_stack(uc, at, size, _):
            if uc.reg_read(r.UC_X86_REG_SS) == data_segment:
                water[0] = min(water[0], uc.reg_read(r.UC_X86_REG_SP))
        cpu.hook_add(UC_HOOK_CODE, measure_stack)
        def release(ss=data_segment):
            seg, off = syms['pc88va_release_boot_memory_']
            cpu.mem_write(0x60000, b'\x9a' + struct.pack('<HH', off, seg + load))
            for reg, value in [(r.UC_X86_REG_CS, 0x6000), (r.UC_X86_REG_IP, 0),
                               (r.UC_X86_REG_DS, data_segment), (r.UC_X86_REG_SS, ss),
                               (r.UC_X86_REG_SP, frame)]:
                cpu.reg_write(reg, value)
            cpu.emu_start(0x60000, 0x60005, count=20000)
            assert cpu.reg_read(r.UC_X86_REG_CS) == 0x6000
            assert cpu.reg_read(r.UC_X86_REG_IP) == 5
            assert cpu.reg_read(r.UC_X86_REG_SP) == frame
            return cpu.reg_read(r.UC_X86_REG_AX)
        setup_release()
        assert release() == 0
        assert cpu.mem_read(root * 16, 5) == struct.pack('<BHH', ord('Z'), 0, ceiling-root-1)
        assert cpu.mem_read(address('_pc88va_boot_mcb'), 2) == b'\0\0'
        assert water[0] >= syms['_p_0_tos'][1] - 192, 'release exceeds permanent stack'
        assert release() != 0, 'release must not free a later child on a second call'
        for case in ('wrong-stack', 'live-buffer', 'bad-owner', 'bad-terminal', 'bad-link'):
            setup_release()
            if case == 'live-buffer':
                cpu.mem_write(address('_firstbuf'), struct.pack('<HH', 0, temporary))
            elif case == 'bad-owner':
                mcb(temporary, ord('Z'), 9, ceiling-temporary-1)
            elif case == 'bad-terminal':
                mcb(temporary, ord('M'), 8, ceiling-temporary-1)
            elif case == 'bad-link':
                mcb(root, ord('M'), 0, temporary-root)
            before = bytes(cpu.mem_read(root * 16, 16)) + bytes(cpu.mem_read(temporary * 16, 16))
            assert release(0x5000 if case == 'wrong-stack' else data_segment) != 0, case
            after = bytes(cpu.mem_read(root * 16, 16)) + bytes(cpu.mem_read(temporary * 16, 16))
            assert before == after, case
        print('LINKED_BOOT_RELEASE_AND_NEGATIVE_LIFETIME_CASES_OK; stack_bytes=' + str(syms['_p_0_tos'][1] - water[0]))
    print('LINKED_PLATFORM_FRAME_AND_CON_CONTRACT_OK')


def verify_init_formatter(kernel, link_map):
    """Execute the linked INIT varargs formatter with a separate stack segment."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_INTR
    from unicorn import x86_const as r
    syms = symbols(link_map)
    _, body, relocations = parse_mz(kernel.read_bytes())
    load = 0x1000
    body = bytearray(body)
    for off, seg in struct.iter_unpack('<HH', relocations):
        at = seg * 16 + off
        struct.pack_into('<H', body, at, struct.unpack_from('<H', body, at)[0] + load)
    cpu = Uc(UC_ARCH_X86, UC_MODE_16)
    cpu.mem_map(0, 0x100000)
    cpu.mem_write(load * 16, bytes(body))
    output = bytearray()
    def interrupt(uc, number, data):
        assert number == 0x29, number
        output.append(uc.reg_read(r.UC_X86_REG_AX) & 255)
    cpu.hook_add(UC_HOOK_INTR, interrupt)
    ds = syms['DATASTART'][0] + load
    # The argument format is in data memory; varargs and local digit buffers
    # are in SS. Neither near-stack aliases nor zero values can pass here.
    cpu.mem_write(ds * 16 + 0xf000, b'%uKB %05lxh %04xh\0')
    cpu.mem_write(0x70800, struct.pack('<HHHHIH', 0, 0x9000, 0xf000, 512, 0x67000, 0x2000))
    seg, off = syms['init_printf_']
    for name, value in dict(CS=seg + load, IP=off, DS=ds, SS=0x7000, SP=0x800).items():
        cpu.reg_write(getattr(r, 'UC_X86_REG_' + name), value)
    cpu.emu_start((seg + load) * 16 + off, 0x90000, count=100000)
    assert output == b'512KB 67000h 2000h', output
    print('LINKED_INIT_FORMATTER_SEPARATE_STACK_OK')


def verify_bridge(kernel, link_map, carrier, record, selected=None, capacity=640, succeeds=True):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_INTR
    from unicorn import x86_const as r
    metadata = json.loads(record.read_text())
    h, linked, fixups = parse_mz(kernel.read_bytes())
    default_load = metadata['definitions']['M13_IMAGE_SEG']
    load = default_load if selected is None else selected
    delta = (load - default_load) * 16
    reference_load = load if succeeds else default_load
    reference_delta = delta if succeeds else 0
    transformed, split = split_image(
        linked, fixups, link_map, reference_load,
        memory_top=metadata['memory_top'],
        init_top=metadata['init_top'] + reference_delta,
        runtime_top=bool(metadata['definitions']['M13_RUNTIME_MEMORY_TOP']))
    if 'M16_LOW_IMAGE_END_PARAS' in metadata['definitions']:
        # Derive the live low envelope independently from the linked MZ.
        extent = max(((len(linked) + 15) // 16 + h[5]) * 16,
                     h[7] * 16 + h[8])
        low_end = (max(reference_load * 16 + extent,
                       split['resident_text'][1]) + 15) & ~15
        assert metadata['definitions']['M16_LOW_IMAGE_END_PARAS'] == (
            low_end // 16 - reference_load)
        if succeeds:
            # Temporary INIT tracks RAM top, not the resident image base.
            # Derive its top independently from the bridge-stack boundary.
            init_top = capacity * 1024 - 0x2000
            transformed, split = split_image(
                linked, fixups, link_map, reference_load,
                memory_top=metadata['memory_top'], init_top=init_top,
                runtime_top=bool(metadata['definitions']['M13_RUNTIME_MEMORY_TOP']))
            assert split['init_stack'][1] == init_top
            assert low_end <= capacity * 1024 - 0x19000
    expected = bytearray(transformed)
    for off, seg in struct.iter_unpack('<HH', fixups):
        at = seg * 16 + off
        value = struct.unpack_from('<H', expected, at)[0]
        struct.pack_into('<H', expected, at, value + load)
    cpu = Uc(UC_ARCH_X86, UC_MODE_16)
    cpu.mem_map(0, 0x100000)
    cpu.mem_write(0, b'\xa5' * 0x100000)
    cpu.mem_write(capacity * 1024, b'\xff' * (0x100000 - capacity * 1024))
    def missing_ram(uc, access, address, size, value, _):
        if address >= capacity * 1024:
            uc.mem_write(address, b'\xff' * size)
    if capacity < 640:
        # Intercept only the absent interval. A read hook on an installed
        # RETF stack perturbs 16-bit far-return IP handling in Unicorn 2.1.4.
        cpu.hook_add(UC_HOOK_MEM_READ, missing_ram, None, capacity * 1024, 0x9ffff)
    cpu.hook_add(UC_HOOK_INTR, lambda uc, interrupt, _: None)
    carrier_base = (capacity * 64 - 0x1900 if 'M16_BOOT_RECORD_OFFSET' in metadata['definitions']
                    else metadata['definitions']['M13_LOAD_SEG'])
    cpu.mem_write(carrier_base * 16, carrier.read_bytes()[32:])
    for reg, value in [(r.UC_X86_REG_CS, carrier_base), (r.UC_X86_REG_IP, 0),
                       (r.UC_X86_REG_SS, carrier_base), (r.UC_X86_REG_SP, metadata['carrier_stack_pointer']),
                       (r.UC_X86_REG_BX, 0 if selected is None else selected),
                       (r.UC_X86_REG_CX, carrier_base),
                       (r.UC_X86_REG_AX, capacity),
                       (r.UC_X86_REG_DX, 0x1234)]:
        cpu.reg_write(reg, value)
    reached = []
    def entry(uc, address, size, _):
        reached.append(address)
        uc.emu_stop()
    target = load * 16 + h[11] * 16 + h[10]
    cpu.hook_add(UC_HOOK_CODE, entry, begin=target, end=target)
    cpu.emu_start(carrier_base * 16, 0xfffff, timeout=30000000, count=5000000)
    if not succeeds:
        assert not reached, 'unsafe placement reached the kernel'
        assert cpu.reg_read(r.UC_X86_REG_AX) == 0x1601, 'missing placement rejection'
        print(f'RUNTIME_PLACEMENT_REJECTED; base={load:04x}; capacity={capacity}')
        return
    assert reached == [target], ('real carrier did not reach the MZ entry',
                                hex(load), capacity,
                                {name: hex(cpu.reg_read(getattr(r, 'UC_X86_REG_' + name)))
                                 for name in ('CS', 'IP', 'AX', 'DS', 'ES', 'SS', 'SP')})
    boot_at = metadata['definitions'].get('M16_BOOT_RECORD_OFFSET')
    if boot_at is not None:
        work_file = carrier_base
        work_ring = work_file + 0x1100
        work_stack = work_file + 0x1000
        wanted = struct.pack('<6H', carrier_base, work_file,
                             work_stack, work_ring, work_stack,
                             metadata['definitions']['M13_BRIDGE_STACK_SP'])
        assert bytes(cpu.mem_read(load * 16 + boot_at, 20)) == b'M16BOOT1' + wanted

    if split:
        actual_descriptor = bytes(cpu.mem_read(split['descriptor'], 24))
        descriptor_words = struct.unpack_from('<8H', actual_descriptor, 8)
        runtime_top = bool(metadata['definitions']['M13_RUNTIME_MEMORY_TOP'])
        expected_descriptor_words = (
            load,
            split['resident_text'][0] // 16,
            split['init'][0] // 16,
            split['init'][1] - split['init'][0],
            split['init_stack'][0] // 16,
            4096,
            0 if runtime_top else metadata['memory_top'] // 16,
            1,
        )
        assert actual_descriptor[:8] == b'M13PLAN1'
        assert descriptor_words == expected_descriptor_words, (
            'unpacked placement descriptor does not match the qualified carrier plan',
            descriptor_words, expected_descriptor_words)
    for source, destination in [('init_source', 'init'), ('hma_source', 'resident_text')]:
        start, end = split[source]
        wanted = expected[start-load*16:end-load*16]
        assert cpu.mem_read(split[destination][0], len(wanted)) == wanted, destination
    assert cpu.mem_read(split['init_stack'][0], 4096) == bytes(4096)
    assert cpu.reg_read(r.UC_X86_REG_SS) == load + h[7]
    assert cpu.reg_read(r.UC_X86_REG_SP) == h[8]
    assert cpu.reg_read(r.UC_X86_REG_DX) == 0x1234
    # Each enumerated fixup is checked at its final owner, including INIT.
    for off, seg in struct.iter_unpack('<HH', fixups):
        at = load * 16 + seg * 16 + off
        destination = at
        for source, target_name in [('init_source', 'init'), ('hma_source', 'resident_text')]:
            lo, hi = split[source]
            if lo <= at < hi:
                destination = split[target_name][0] + at - lo
                break
        assert cpu.mem_read(destination, 2) == expected[at-load*16:at-load*16+2]
    print(f'REAL_SPLIT_BRIDGE_AND_ALL_FINAL_FIXUPS_OK; base={load:04x}; capacity={capacity}')


def verify_model_banner(kernel, link_map):
    """Execute the linked INIT banner with synthetic model/board registers."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, UC_HOOK_INSN
    from unicorn import x86_const as r
    syms = symbols(link_map)
    _, body, relocations = parse_mz(kernel.read_bytes())
    load = 0x1000
    body = bytearray(body)
    for off, seg in struct.iter_unpack('<HH', relocations):
        at = seg * 16 + off
        struct.pack_into('<H', body, at, struct.unpack_from('<H', body, at)[0] + load)
    entry_seg, entry_off = syms['_pc88va_print_model']
    put_seg, put_off = syms['pc88va_diag_putc_']
    put_address = (put_seg + load) * 16 + put_off
    for model, board, expected in (
            (0xffff, 0xff, 'Machine = VA\r\n'),
            (0xfffe, 0xff, 'Machine = VA2/3\r\n'),
            (0xffff, 0x7f, 'Machine = VA + verup board (PC-88VA-91)\r\n'),
            (0x1234, 0xff, 'Machine = Unknown\r\n')):
        cpu = Uc(UC_ARCH_X86, UC_MODE_16)
        cpu.mem_map(0, 0x100000)
        cpu.mem_write(load * 16, bytes(body))
        cpu.mem_write(0xffffe, struct.pack('<H', model))
        cpu.mem_write(put_address, b'\xcb')  # capture output, then FAR return
        cpu.mem_write(0x60000, b'\x9a' + struct.pack('<HH', entry_off, entry_seg + load))
        bank, writes, output = [0xa5], [], []
        def port_in(uc, port, size, _):
            assert size == 1 and port in (0x152, 0x156)
            return bank[0] if port == 0x152 else board
        def port_out(uc, port, size, value, _):
            assert port == 0x152 and size == 1
            assert not uc.reg_read(r.UC_X86_REG_EFLAGS) & 0x200
            bank[0] = value
            writes.append(value)
        def capture(uc, at, size, _):
            if at == put_address:
                assert bank[0] == 0xa5
                output.append(uc.reg_read(r.UC_X86_REG_AX) & 255)
                uc.reg_write(r.UC_X86_REG_AX, 0)
        cpu.hook_add(UC_HOOK_INSN, port_in, None, 1, 0, r.UC_X86_INS_IN)
        cpu.hook_add(UC_HOOK_INSN, port_out, None, 1, 0, r.UC_X86_INS_OUT)
        cpu.hook_add(UC_HOOK_CODE, capture)
        saved = [(r.UC_X86_REG_AX, 0x1234), (r.UC_X86_REG_BX, 0x2345),
                 (r.UC_X86_REG_CX, 0x3456), (r.UC_X86_REG_DX, 0x4567),
                 (r.UC_X86_REG_SI, 0x5678), (r.UC_X86_REG_DI, 0x6789),
                 (r.UC_X86_REG_BP, 0x789a), (r.UC_X86_REG_DS, 0x1070),
                 (r.UC_X86_REG_ES, 0x8000), (r.UC_X86_REG_SS, 0x7000),
                 (r.UC_X86_REG_SP, 0x1000), (r.UC_X86_REG_EFLAGS, 0x202)]
        for reg, value in saved:
            cpu.reg_write(reg, value)
        cpu.reg_write(r.UC_X86_REG_CS, 0x6000)
        cpu.reg_write(r.UC_X86_REG_IP, 0)
        cpu.emu_start(0x60000, 0x60005, count=20000)
        assert cpu.reg_read(r.UC_X86_REG_CS) == 0x6000
        assert cpu.reg_read(r.UC_X86_REG_IP) == 5
        assert bytes(output).decode('ascii') == expected
        assert writes == [0x05, 0xa5]
        for reg, value in saved:
            assert cpu.reg_read(reg) == value, (expected, reg)
    print('INIT_MODEL_BANNER_BRANCHES_AND_BANK_RESTORE_OK')


def verify_resident_disk_capacity(kernel, link_map):
    """Check real linked read/write wrappers and cores against buffer guards."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
    from unicorn import x86_const as r
    syms = symbols(link_map)
    _, body, relocations = parse_mz(kernel.read_bytes())
    body = bytearray(body)
    load = 0x1000
    for off, seg in struct.iter_unpack('<HH', relocations):
        at = seg * 16 + off
        struct.pack_into('<H', body, at, struct.unpack_from('<H', body, at)[0] + load)
    platform, buffer_off = syms['pc88va_m12_buffer_']
    platform += load
    def addr(name):
        seg, off = syms[name]
        return (seg + load) * 16 + off
    buffer_at = platform * 16 + buffer_off
    assert addr('pc88va_m12_storage_end') - buffer_at == 1024
    request_at = addr('pc88va_m12_request_')
    for operation in ('read', 'write'):
        for sector, count, capacity, status in (
                (512, 1, 1024, 0), (1024, 1, 1024, 0),
                (1024, 2, 1024, 3), (2048, 1, 1024, 3),
                (1024, 1, 4096, 1)):
            cpu = Uc(UC_ARCH_X86, UC_MODE_16)
            cpu.mem_map(0, 0x100000)
            cpu.mem_write(load * 16, bytes(body))
            cpu.mem_write(addr('pc88va_m10_state_'), b'\x02')
            fields = [1, 0, count, buffer_off, platform, capacity,
                      1280, 8, 2, sector, 0, 0, 0x6000, 0] + [0] * 10
            cpu.mem_write(request_at, struct.pack('<24H', *fields))
            # The preceding byte belongs to alignment/data; use a canary only
            # inside this synthetic snapshot, without changing the executable.
            cpu.mem_write(buffer_at - 1, b'\xa5')
            cpu.mem_write(buffer_at, b'\x5a' * 1024)
            cpu.mem_write(buffer_at + 1024, b'\xa5' * 16)
            cpu.mem_write(0x60000, b'\x31\xc0\xb9' + struct.pack('<H', sector) + b'\xcb')
            callbacks = []
            def transfer(uc, at, size, _):
                if at == 0x60000:
                    off, seg = struct.unpack('<HH', uc.mem_read(request_at + 38, 4))
                    target = seg * 16 + off
                    assert buffer_at <= target and target + sector <= buffer_at + 1024
                    callbacks.append(target)
                    if operation == 'read':
                        uc.mem_write(target, b'\x3c' * sector)
                    else:
                        assert uc.mem_read(target, sector) == b'\x5a' * sector
            cpu.hook_add(UC_HOOK_CODE, transfer)
            entry_seg, entry_off = syms['pc88va_kernel_disk_' + operation + '_']
            assert entry_seg + load == platform
            for reg, value in ((r.UC_X86_REG_CS, platform), (r.UC_X86_REG_IP, entry_off),
                               (r.UC_X86_REG_DS, platform), (r.UC_X86_REG_SS, 0x7000),
                               (r.UC_X86_REG_SP, 0x1000), (r.UC_X86_REG_EFLAGS, 2),
                               (r.UC_X86_REG_AX, syms['pc88va_m12_request_'][1])):
                cpu.reg_write(reg, value)
            cpu.mem_write(0x71000, struct.pack('<H', 0xfff0))
            cpu.emu_start(platform * 16 + entry_off, platform * 16 + 0xfff0, count=20000)
            assert cpu.reg_read(r.UC_X86_REG_IP) == 0xfff0
            assert cpu.reg_read(r.UC_X86_REG_AX) == status
            assert len(callbacks) == (1 if status == 0 else 0)
            assert cpu.mem_read(buffer_at - 1, 1) == b'\xa5'
            assert cpu.mem_read(buffer_at + 1024, 16) == b'\xa5' * 16
    print('RESIDENT_ONE_SECTOR_BUFFER_READ_WRITE_BOUNDS_OK')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--map', type=Path, required=True)
    parser.add_argument('--carrier', type=Path)
    parser.add_argument('--placement', type=Path)
    args = parser.parse_args()
    verify(args.kernel, args.map)
    verify_init_formatter(args.kernel, args.map)
    verify_model_banner(args.kernel, args.map)
    verify_resident_disk_capacity(args.kernel, args.map)
    if args.carrier:
        for capacity in (256, 384, 511, 512, 640):
            verify_bridge(args.kernel, args.map, args.carrier, args.placement, capacity=capacity)
        for selected in (0x2000, 0x3000, 0x4000, 0x5000):
            verify_bridge(args.kernel, args.map, args.carrier, args.placement, selected, 512)
        for selected, capacity in ((0x0800, 512), (0x6000, 512), (0x2000, 256)):
            verify_bridge(args.kernel, args.map, args.carrier, args.placement, selected, capacity, False)
