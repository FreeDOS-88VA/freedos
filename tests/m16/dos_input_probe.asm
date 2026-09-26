; SPDX-License-Identifier: GPL-2.0-or-later
; DOS-level input probe. It captures complete AH=07h bytes into KEYINPUT.BIN.
bits 16
org 100h

%define INPUT_BYTES 71

start:
        push cs
        pop ds
        mov dx, ready_message
        mov ah, 09h
        int 21h

        mov word [input_index], 0
        mov word [input_remaining], INPUT_BYTES
.read_key:
        mov ah, 07h
        int 21h
        mov bx, [input_index]
        mov [input_buffer+bx], al
        inc word [input_index]
        dec word [input_remaining]
        jnz .read_key

        mov dx, output_name
        xor cx, cx
        mov ah, 3ch
        int 21h
        jc .error
        mov [output_handle], ax

        mov bx, ax
        mov cx, INPUT_BYTES
        mov dx, input_buffer
        mov ah, 40h
        int 21h
        jc .write_close_error
        cmp ax, INPUT_BYTES
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

ready_message db 'M16 INPUT READY',13,10,'$'
done_message db 'M16 INPUT DONE',13,10,'$'
error_message db 'M16 INPUT ERROR',13,10,'$'
output_name db 'KEYINPUT.BIN',0
output_handle dw 0
input_index dw 0
input_remaining dw 0
input_buffer times INPUT_BYTES db 0
