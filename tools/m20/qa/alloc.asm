; SPDX-License-Identifier: GPL-2.0-or-later
; QA only. Own-process allocations; never edits another owner's MCB.
; Checks the pinned FreeDOS allocation contract, not MS-DOS equivalence.
bits 16
cpu 8086
org 100h
start:
        cli
        mov ax, cs
        mov ss, ax
        mov sp, stack_top
        sti
        mov ds, ax
        mov es, ax
        mov [psp], ax
        mov bx, (stack_top - $$ + 100h + 15) / 16
        mov ah, 4ah
        int 21h
        jc fail
        mov byte [stage], 2
        mov ax, 5800h
        int 21h
        jc fail
        mov [strategy], ax
        mov byte [have_strategy], 1
        mov ax, 5801h
        xor bx, bx              ; first fit, restored at exit
        int 21h
        jc fail
        call largest
        mov [baseline], bx
        mov dx, baseline_text
        mov ah, 09h
        int 21h
        call hex_word
        mov dx, newline
        mov ah, 09h
        int 21h
        mov word [rounds], 16
round:
        mov byte [stage], 3
        mov bx, 32
        call allocate
        mov [block_a], ax
        call allocate
        mov [block_b], ax
        call allocate
        mov [block_c], ax
        ; Bound fragmentation: consume the large tail so it cannot mask a
        ; failure to coalesce the deliberately adjacent small allocations.
        call largest
        call allocate
        mov [guard], ax
        mov byte [stage], 4
        mov ax, [block_a]
        mov es, ax
        mov word [es:0], 1234h
        mov ax, [block_c]
        mov es, ax
        mov word [es:0], 5678h
        mov byte [stage], 5
        mov ax, [block_a]
        mov es, ax
        mov bx, 16
        mov ah, 4ah
        int 21h
        jc fail
        mov bx, 32
        mov ah, 4ah
        int 21h
        jc fail
        mov byte [stage], 6
        mov bx, 64
        mov ah, 4ah
        int 21h
        jnc fail
        cmp ax, 8
        jne fail
        cmp bx, 32
        jne fail
        cmp word [es:0], 1234h
        jne fail
        mov byte [stage], 7
        mov ax, [block_b]
        call release
        mov ax, [block_a]
        mov es, ax
        mov bx, 65              ; two payloads and the retired MCB paragraph
        mov ah, 4ah
        int 21h
        jc fail
        mov byte [stage], 8
        mov ax, [block_c]
        mov es, ax
        cmp word [es:0], 5678h
        jne fail
        dec ax
        mov es, ax
        mov ax, [psp]
        cmp [es:1], ax
        jne fail
        cmp word [es:3], 32
        jne fail
        mov byte [stage], 9
        ; Invalid handles point into our own payload, whose type byte is
        ; deliberately not M/Z. No live MCB is corrupted to test rejection.
        mov ax, [block_a]
        inc ax
        mov es, ax
        mov bx, 16
        mov ah, 4ah
        int 21h
        jnc fail
        cmp ax, 7              ; pinned FreeDOS: DE_MCBDESTRY
        jne fail
        mov ah, 49h
        int 21h
        jnc fail
        cmp ax, 9              ; pinned FreeDOS: DE_INVLDMCB
        jne fail
        mov byte [stage], 10
        mov ax, [block_a]
        call release
        mov ax, [block_c]
        call release
        mov bx, 98              ; three payloads, two retired headers
        call allocate
        cmp ax, [block_a]
        jne fail
        call release
        mov ax, [guard]
        call release
        mov byte [stage], 11
        xor bx, bx              ; zero payload is legal, not a corrupt MCB
        call allocate
        mov [zero_block], ax
        dec ax
        mov es, ax
        cmp word [es:3], 0
        jne fail
        mov ax, [psp]
        cmp [es:1], ax
        jne fail
        mov ax, [zero_block]
        call release
        call largest
        cmp bx, [baseline]
        jne fail
        dec word [rounds]
        jnz round
        mov byte [stage], 12
        call largest
        call allocate          ; exact reported largest block must be usable
        mov [guard], ax
        mov es, ax
        mov word [es:0], 1357h
        mov dx, ax
        add dx, bx
        dec dx
        mov es, dx
        mov word [es:14], 2468h ; last word of the last owned paragraph
        mov byte [stage], 13
        mov bx, [baseline]
        inc bx
        mov ah, 48h
        int 21h
        jnc fail
        cmp ax, 8
        jne fail
        mov ax, [guard]
        mov es, ax
        cmp word [es:0], 1357h
        jne fail
        mov es, dx
        cmp word [es:14], 2468h
        jne fail
        mov ax, [guard]
        call release
        call largest
        cmp bx, [baseline]
        jne fail
        call restore_strategy
        mov dx, passed
        mov ah, 09h
        int 21h
        mov ax, 4c00h
        int 21h

; BX request/result retained; AX contains the allocated payload segment.
allocate:
        mov ah, 48h
        int 21h
        jc fail
        push es
        push ax
        dec ax
        mov es, ax
        cmp [es:3], bx
        jne fail
        mov ax, [psp]
        cmp [es:1], ax
        jne fail
        pop ax
        pop es
        ret
release:
        mov es, ax
        mov ah, 49h
        int 21h
        jc fail
        ret
largest:
        mov bx, 0ffffh
        mov ah, 48h
        int 21h
        jnc fail
        cmp ax, 8
        jne fail
        or bx, bx
        jz fail
        ret
restore_strategy:
        cmp byte [have_strategy], 0
        je .done
        mov bx, [strategy]
        mov ax, 5801h
        int 21h
.done:  ret
fail:
        ; DOS termination frees only this child's blocks, including any
        ; outstanding QA blocks after an assertion failure.
        mov ax, cs
        mov ds, ax
        call restore_strategy
        mov dx, failed
        mov ah, 09h
        int 21h
        mov al, [stage]
        xor ah, ah
        mov bl, 10
        div bl
        mov [digit], ah
        mov dl, al
        add dl, '0'
        mov ah, 02h
        int 21h
        mov dl, [digit]
        add dl, '0'
        mov ah, 02h
        int 21h
        mov dx, newline
        mov ah, 09h
        int 21h
        mov ax, 4c01h
        int 21h
hex_word:
        push ax
        push bx
        push cx
        push dx
        mov cx, 4
.next:
        rol bx, 1
        rol bx, 1
        rol bx, 1
        rol bx, 1
        mov dl, bl
        and dl, 15
        add dl, '0'
        cmp dl, '9'
        jbe .emit
        add dl, 7
.emit:
        mov ah, 02h
        int 21h
        loop .next
        pop dx
        pop cx
        pop bx
        pop ax
        ret
baseline_text db 'ALLOC baseline largest payload (hex paragraphs): $'
passed db 'ALLOC: PASS (16 allocation/resize/coalescing rounds; largest block)',13,10,'$'
failed db 'ALLOC: FAIL stage $'
newline db 13,10,'$'
psp dw 0
strategy dw 0
have_strategy db 0
stage db 1
digit db 0
baseline dw 0
rounds dw 0
block_a dw 0
block_b dw 0
block_c dw 0
guard dw 0
zero_block dw 0
align 16, db 0
stack_bottom:
        times 512 db 0
stack_top:
