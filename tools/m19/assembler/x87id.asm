; SPDX-License-Identifier: GPL-2.0-or-later
; PC-88VA replacement for the Open Watcom 1.9 clibl.lib(init8087) module.
;
; The pinned OW 1.9 __x87id starts with "FWAIT; FNINIT".  On an 8086-class
; CPU without a coprocessor, FWAIT waits for the CPU TEST/POLL input.  On the
; PC-88VA without an x87 that input need not be asserted, so the original
; detector can stop before main() and before NO87 is honored.  This module
; probes with the no-wait forms first, as Intel recommends, and only uses
; waiting forms after a coprocessor has answered.  The public interface and
; return values are unchanged: AL = 0 (none), 2 (8087/80287) or 3 (80387),
; AH = 0; BX, CX, DX, SI, DI and segment registers are preserved.
;
; Linking this object before the C library keeps the library init8087 module
; (and its waiting probe) out of JWASMR.EXE.  All other emulator, strtod and
; NO87 behavior stays the pinned OW 1.9 runtime.
bits 16
cpu 8086

segment _TEXT public class=CODE use16

global __x87id, __init_8087_emu
extern __init_8087_

; Same body as the library module: call the C runtime FPU initializer.
__init_8087_emu:
        push cs
        call __init_8087_
        nop
        ret

__x87id:
        push bp
        mov bp, sp
        push cx
        sub ax, ax
        push ax                 ; [bp-4] = 0: no coprocessor writes it
        fninit                  ; DB E3, no WAIT prefix
        mov cx, 64
.settle1:
        loop .settle1
        fnstcw [bp-4]           ; D9 7E FC, no WAIT prefix
        mov cx, 64
.settle2:
        loop .settle2
        pop ax
        mov al, 0
        cmp ah, 3               ; FNINIT control word high byte is 03h
        jne .done
        ; A coprocessor answered; its BUSY drives TEST, so WAIT is safe.
        ; An 8087 needs WAIT before each ESC, as in the library sequence.
        push ax
        fwait
        fld1
        fwait
        fldz
        fwait
        fdivp st1               ; +infinity
        fwait
        fld st0
        fwait
        fchs                    ; -infinity
        fwait
        fcompp                  ; 8087/80287 projective: equal; 80387: not
        fwait
        fnstsw [bp-4]
        fwait
        pop ax
        mov al, 2
        sahf
        jz .reinit
        mov al, 3
.reinit:
        fninit
.done:
        mov ah, 0
        pop cx
        mov sp, bp
        pop bp
        ret
