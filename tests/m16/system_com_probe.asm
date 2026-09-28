; SPDX-License-Identifier: GPL-2.0-or-later
; M13 public COM probe.  It uses only DOS INT 21h services: command-tail
; inspection, file open/read/close, stdout, and a non-zero exit code.
bits 16
org 100h
start:
        xor cx, cx
        mov cl, [80h]               ; obtain the actual DOS command-tail size
        jcxz .no_args
        mov si, 81h
        add si, cx
        mov byte [si], '$'          ; PSP tail is caller-owned program memory
        mov dx, 81h
        mov ah, 09h
        int 21h                     ; output the actual argument through DOS
.no_args:
        mov dx, filename
        mov al, 0
        mov ah, 3dh                 ; open fixture file read-only
        int 21h
        jc .open_failed
        mov bx, ax
        mov dx, buffer
        mov cx, buffer_end-buffer
        mov ah, 3fh                 ; read through DOS handle path
        int 21h
        pushf
        push ax                     ; preserve byte count for output
        mov ah, 3eh                 ; close handle
        int 21h
        pop cx
        popf
        jc .read_failed
        mov dx, buffer
        mov bx, 1
        mov ah, 40h                 ; write bytes to inherited stdout
        int 21h
        mov ax, 4c11h               ; independently observed non-zero status
        int 21h
.open_failed:
        mov ax, 4c21h
        int 21h
.read_failed:
        mov ax, 4c22h
        int 21h
filename db 'COMDATA.TXT', 0
buffer times 128 db 0
buffer_end:
