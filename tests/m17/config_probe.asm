; SPDX-License-Identifier: GPL-2.0-or-later
bits 16
cpu 8086
org 0x100
    mov ax,0x3d00
    mov dx,device
    int 21h
    jc failed
    mov bx,ax
    mov ah,0x3e
    int 21h
    jc failed
    mov dx,ok
    jmp print
failed:
    mov dx,bad
print:
    mov ah,9
    int 21h
    mov ax,0x4c00
    int 21h
device: db 'VA17TEST',0
ok: db 'M17-DEVICE-OPEN-OK',13,10,'$'
bad: db 'M17-DEVICE-OPEN-FAILED',13,10,'$'
