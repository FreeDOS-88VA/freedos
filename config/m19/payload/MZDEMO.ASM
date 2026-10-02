; MZDEMO.ASM -- a self-contained 8086 DOS MZ program.
.8086
.model small
.stack 512
.data
message db 'MZ relocation and DOS return succeeded.',13,10,'$'
.code
start:
    mov ax, @data
    mov ds, ax
    mov dx, offset message
    mov ah, 09h
    int 21h
    mov ax, 4c00h
    int 21h
end start
