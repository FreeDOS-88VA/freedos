; HELLO.ASM -- a self-contained 8086 DOS COM program.
.8086
.model tiny
.code
org 100h
start:
    mov dx, offset message
    mov ah, 09h
    int 21h
    mov ax, 4c00h
    int 21h
message db 'Hello from PC-88VA FreeDOS!',13,10,'$'
end start
