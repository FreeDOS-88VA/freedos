; SPDX-License-Identifier: GPL-2.0-or-later
; Read actual DOS configuration through INT 21h/AH=52h.
bits 16
cpu 8086
org 0x100
    mov ah,0x52
    int 0x21
    mov ax,[es:bx+0x3f]
    mov [buffers],ax
    xor ax,ax
    mov al,[es:bx+0x21]
    mov [last],ax
    mov al,[es:bx+0x20]
    mov [units],ax
    les bx,[es:bx+4]
    mov cx,16
    xor si,si
.next:
    add si,[es:bx+4]
    cmp word [es:bx],0xffff
    je .end
    les bx,[es:bx]
    loop .next
    mov si,0xffff
.end:
    mov [files],si
    mov dx,label_buffers
    mov ax,[buffers]
    call field
    mov dx,label_last
    mov ax,[last]
    call field
    mov dx,label_files
    mov ax,[files]
    call field
    mov dx,label_units
    mov ax,[units]
    call field
    mov dx,newline
    mov ah,9
    int 21h
    mov ax,0x4c00
    int 21h
field:
    push ax
    mov ah,9
    int 21h
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
    int 21h
    pop cx
    loop .digit
    ret
buffers: dw 0
last: dw 0
files: dw 0
units: dw 0
label_buffers: db 'BUFFERS=$'
label_last: db ' LAST=$'
label_files: db ' FILES=$'
label_units: db ' UNITS=$'
newline: db 13,10,'$'
