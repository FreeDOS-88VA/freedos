; SPDX-License-Identifier: GPL-2.0-or-later
; M13 public MZ probe.  The data/stack references intentionally require a
; relocation entry; EXEC must apply it before this DOS INT 21h-only program.
bits 16
cpu 8086
segment CODE class=CODE
..start:
        mov ax, DATA
        mov ds, ax
        mov dx, message
        mov ah, 09h
        int 21h
        mov ax, [return_value]
        mov ah, 4ch
        int 21h
segment DATA class=DATA
message db 'MZ-RELOCATED', 13, 10, '$'
return_value dw 19
segment STACK class=STACK stack
        resb 256
