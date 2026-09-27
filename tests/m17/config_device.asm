; SPDX-License-Identifier: GPL-2.0-or-later
; A disposable character driver for actual CONFIG.SYS DEVICE= qualification.
bits 16
cpu 8086
org 0
header:
    dd 0xffffffff
    dw 0x8000
    dw strategy, interrupt
    db 'VA17TEST'
packet: dd 0
strategy:
    mov [cs:packet], bx
    mov [cs:packet+2], es
    retf
interrupt:
    push ax
    push bx
    push dx
    push ds
    push es
    les bx, [cs:packet]
    mov word [es:bx+3], 0x0100
    cmp byte [es:bx+2], 0
    je init
    cmp byte [es:bx+2], 4
    je eof
    cmp byte [es:bx+2], 8
    je done
    cmp byte [es:bx+2], 0x0d
    je done
    cmp byte [es:bx+2], 0x0e
    je done
    mov word [es:bx+3], 0x8103
    jmp done
eof:
    mov word [es:bx+18], 0
    jmp done
init:
    mov word [es:bx+14], resident_end
    mov [es:bx+16], cs
    push cs
    pop ds
    mov dx, message
    mov ah, 9
    int 21h
done:
    pop es
    pop ds
    pop dx
    pop bx
    pop ax
    retf
message: db 'M17-DEVICE-INIT',13,10,'$'
resident_end:
