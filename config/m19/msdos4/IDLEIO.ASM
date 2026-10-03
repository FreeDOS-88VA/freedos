; SPDX-License-Identifier: GPL-2.0-or-later
; Hold a reader and a dirty writer open across five DOS clock second changes.
.8086
.model tiny
.code
org 100h
start:
    push cs
    pop ds
    push cs
    pop es
    mov ax, 3d00h
    mov dx, offset source_name
    int 21h
    jc failed
    mov reader, ax
    mov bx, ax
    mov ah, 3fh
    mov cx, 16
    mov dx, offset first
    int 21h
    jc failed
    cmp ax, 16
    jne failed
    mov ah, 3ch
    xor cx, cx
    mov dx, offset output_name
    int 21h
    jc failed
    mov writer, ax
    mov bx, ax
    mov ah, 40h
    mov cx, before_end-before
    mov dx, offset before
    int 21h
    jc failed
    cmp ax, before_end-before
    jne failed

    mov ah, 2ch
    int 21h
    mov bl, dh
    mov bp, 5
wait_second:
    mov ah, 2ch
    int 21h
    cmp dh, bl
    je wait_second
    mov bl, dh
    dec bp
    jnz wait_second

    mov bx, reader
    mov ax, 4200h
    xor cx, cx
    xor dx, dx
    int 21h
    jc failed
    mov ah, 3fh
    mov cx, 16
    mov dx, offset second
    int 21h
    jc failed
    cmp ax, 16
    jne failed
    mov si, offset first
    mov di, offset second
    mov cx, 16
    cld
    repe cmpsb
    jne failed
    mov bx, writer
    mov ah, 40h
    mov cx, after_end-after
    mov dx, offset after
    int 21h
    jc failed
    cmp ax, after_end-after
    jne failed
    mov ah, 3eh
    int 21h
    jc failed
    mov bx, reader
    mov ah, 3eh
    int 21h
    jc failed
    mov bx, 1
    mov ah, 40h
    mov cx, success_end-success
    mov dx, offset success
    int 21h
    jc failed
    cmp ax, success_end-success
    jne failed
    mov ax, 4c00h
    int 21h
failed:
    mov bx, 2
    mov ah, 40h
    mov cx, failure_end-failure
    mov dx, offset failure
    int 21h
    mov ax, 4c01h
    int 21h
source_name db 'HELLO.ASM',0
output_name db 'IDLE.DAT',0
before db 'BEFORE',13,10
before_end label byte
after db 'AFTER',13,10
after_end label byte
success db 'IDLEOK',13,10
success_end label byte
failure db 'IDLEFAIL',13,10
failure_end label byte
reader dw 0
writer dw 0
first db 16 dup (0)
second db 16 dup (0)
end start
