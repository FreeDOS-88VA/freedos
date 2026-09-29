; SPDX-License-Identifier: GPL-2.0-or-later
; Original near-limit EXEC fixture. Exit 42 only after real execution.
cpu 8086
bits 16
%ifdef M18_MZ
org 0
header:
        dw 5a4dh
        dw (file_end - header) % 512
        dw (file_end - header + 511) / 512
        dw 1                         ; one actual segment relocation
        dw 4                         ; 64-byte header
        dw 32, 32                    ; bounded extra stack allocation
        dw 0                         ; SS relative to load module
        dw ((file_end - image + 15) & ~15) + 512 - 2
        dw 0                         ; checksum
        dw 0, 0                      ; IP, CS
        dw relocations - header
        dw 0                         ; overlay
relocations:
        dw segment_fixup - image, 0
        times 64 - ($ - header) db 0
image:
        db 0b8h                      ; mov ax, relocated load segment
segment_fixup:
        dw 0
        mov dx, cs
        cmp ax, dx
        jne bad_relocation
        mov ds, ax
        mov ax, 4c2ah
        int 21h
bad_relocation:
        mov ax, 4c01h
        int 21h
file_end:
%else
org 100h
image:
        mov ax, 4c2ah
        int 21h
        ; A complete paragraph keeps the pinned COM loader's minimum at
        ; least 17 paragraphs, including the PSP and initial stack word.
        times 16 - ($ - image) db 0
%endif
