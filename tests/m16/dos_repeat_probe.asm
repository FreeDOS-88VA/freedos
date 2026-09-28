; SPDX-License-Identifier: GPL-2.0-or-later
; Capture DOS AH=07h input until Return; host inspection checks repeat timing.
bits 16
org 100h

%define INPUT_CAPACITY 128

start:
        push cs
        pop ds
        mov dx, ready_message
        mov ah, 09h
        int 21h

        mov word [input_count], 0
.read_key:
        mov ah, 07h
        int 21h
        cmp al, 0dh
        je .write_file
        mov bx, [input_count]
        cmp bx, INPUT_CAPACITY
        jae .error
        mov [input_buffer+bx], al
        inc word [input_count]
        jmp .read_key

.write_file:
        mov dx, output_name
        xor cx, cx
        mov ah, 3ch
        int 21h
        jc .error
        mov [output_handle], ax

        mov bx, ax
        mov cx, [input_count]
        mov dx, input_buffer
        mov ah, 40h
        int 21h
        jc .write_close_error
        cmp ax, [input_count]
        jne .write_close_error
        mov bx, [output_handle]
        mov ah, 3eh
        int 21h
        jc .error

        mov dx, done_message
        mov ah, 09h
        int 21h
        mov ax, 4c00h
        int 21h

.write_close_error:
        mov bx, [output_handle]
        mov ah, 3eh
        int 21h
.error:
        mov dx, error_message
        mov ah, 09h
        int 21h
        mov ax, 4c01h
        int 21h

ready_message db 'M16 REPEAT READY',13,10,'$'
done_message db 'M16 REPEAT DONE',13,10,'$'
error_message db 'M16 REPEAT ERROR',13,10,'$'
output_name db 'REPEAT.BIN',0
output_handle dw 0
input_count dw 0
input_buffer times INPUT_CAPACITY db 0
