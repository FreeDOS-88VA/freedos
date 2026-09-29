; SPDX-License-Identifier: GPL-2.0-or-later
bits 16
cpu 8086
segment _TEXT public class=CODE use16
global _m18_abs_sector, m18_critical_

; unsigned m18_abs_sector(unsigned writing, unsigned drive,
;                         unsigned sector, void __far *buffer)
; The 16:16 far pointer is passed as offset then segment. DOS INT 25h/26h
; use the drive in AX, sector in DX, count in CX and DS:BX.
; DOS leaves the original caller FLAGS on the stack, not the result flags.
; Discard that word without changing live CF. Transfer one 1024-byte sector.
_m18_abs_sector:
        push bp
        mov bp, sp
        push bx
        push cx
        push dx
        push si
        push di
        push ds
        push es
        mov ax, [bp+8]
        mov bx, [bp+12]
        mov dx, [bp+10]
        mov cx, 1
        mov si, [bp+14]
        mov ds, si
        cmp word [bp+6], 0
        jne .write
        int 25h
        jmp short .returned
.write:
        int 26h
.returned:
        pop si                  ; Discard original FLAGS; POP preserves CF.
        jc .failed
        xor ax, ax
        jmp short .done
.failed:
        or ax, ax
        jnz .done
        mov ax, 1
.done:
        pop es
        pop ds
        pop di
        pop si
        pop dx
        pop cx
        pop bx
        pop bp
        retf

m18_critical_:
        mov al, 3               ; Fail; never recurse into DOS error handling.
        iret
