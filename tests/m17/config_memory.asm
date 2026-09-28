; SPDX-License-Identifier: GPL-2.0-or-later
; Report DOS's largest allocatable block after CONFIG.SYS initialization.
bits 16
cpu 8086
org 0x100
    mov ax,0x4800
    mov bx,0xffff
    int 0x21
    jc .largest
    mov es,ax
    mov ah,0x49
    int 0x21
    mov bx,0xffff
    mov dx,unexpected
    jmp .print
.largest:
    mov dx,label
.print:
    mov ax,bx
    call hex16
    mov dx,newline
    mov ah,9
    int 0x21
    mov ax,0x4c00
    int 0x21
hex16:
    push ax
    mov ah,9
    int 0x21
    pop bx
    mov cx,4
.digit:
    push cx
    mov cl,4
    rol bx,cl
    mov dl,bl
    and dl,15
    add dl,'0'
    cmp dl,'9'
    jbe .emit
    add dl,7
.emit:
    mov ah,2
    int 0x21
    pop cx
    loop .digit
    ret
label: db 'MAXFREE_PARAS=$'
unexpected: db 'ALLOC_UNEXPECTED=$'
newline: db 13,10,'$'
