; HELLO.ASM -- a self-contained 8086 DOS COM program.
; On a writable disk, in the directory containing this source, build and run:
;   JWASMR -0 -bin -Fo=HELLO.COM HELLO.ASM
;   HELLO.COM
; This writes a raw COM file directly; no separate linker is required.
; The tested small assembly workflow needs 640 KiB of installed RAM.
; See HELLO.DOC for an explanation and the full build steps.
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
