; SPDX-License-Identifier: GPL-2.0-or-later
; Original 8086 real-DOS near-limit COM/MZ EXEC and recovery probe.
; Allocate only through DOS, retain every live owner, never edit an MCB.
cpu 8086
bits 16
org 100h
start:
        cli
        mov ax, cs
        mov ss, ax
        mov sp, stack_top
        sti
        mov ds, ax
        mov es, ax
        mov [parameters + 4], ax
        mov [parameters + 8], ax
        mov [parameters + 12], ax
        add ax, (empty_environment - $$ + 100h) / 16
        mov [parameters], ax
        mov bx, (stack_top - $$ + 100h + 15) / 16
        mov ah, 4ah
        int 21h
        jc fail
        inc word [stage]              ; 2: save and select first fit
        mov ax, 5800h
        int 21h
        jc fail
        mov [strategy], ax
        mov byte [have_strategy], 1
        mov ax, 5801h
        xor bx, bx
        int 21h
        jc fail
        inc word [stage]              ; 3: establish baseline
        call largest
        cmp bx, 512
        jb fail
        mov [baseline], bx
        inc word [stage]              ; 4: own every positive free block
.reserve:
        call largest
        or bx, bx
        jz .reserved
        cmp word [count], 32
        jae fail
        mov ah, 48h
        int 21h
        jc fail
        mov si, [count]
        shl si, 1
        mov [blocks + si], ax
        inc word [count]
        mov es, ax
        dec ax
        push es
        mov es, ax
        mov ax, cs
        cmp [es:1], ax
        pop es
        jne fail
        mov word [es:0], 0a55ah
        jmp .reserve
.reserved:
        mov dx, exhaustion_text
        mov ah, 09h
        int 21h
        inc word [stage]              ; 5: no-memory rejection for both formats
        mov dx, com_name
        call execute
        or al, al
        jnz fail
        mov dx, mz_name
        call execute
        or al, al
        jnz fail
.boundary:
        mov word [stage], 6           ; controlled tail, all other holes owned
        inc word [budget]
        cmp word [budget], 128
        ja fail
        test word [budget], 15
        jnz .resize
        mov dx, boundary_text
        mov ah, 09h
        int 21h
        mov bx, [budget]
        call hex_word
        mov dx, newline
        mov ah, 09h
        int 21h
.resize:
        mov es, [blocks]
        mov bx, [baseline]
        sub bx, [budget]
        dec bx                       ; newly free MCB itself costs one paragraph
        mov ah, 4ah
        int 21h
        jc fail
        mov word [stage], 7
        mov dx, com_name
        call execute
        or al, al
        jnz .com_ok
        cmp word [com_min], 0
        jne fail                     ; success must not revert to no-memory
        jmp .mz
.com_ok:
        cmp word [com_min], 0
        jne .mz
        mov ax, [budget]
        mov [com_min], ax
.mz:
        mov dx, mz_name
        call execute
        or al, al
        jnz .mz_ok
        cmp word [mz_min], 0
        jne fail
        jmp .boundary
.mz_ok:
        mov ax, [budget]
        mov [mz_min], ax
        cmp word [com_min], 0
        je fail
        cmp ax, [com_min]
        jbe fail                     ; this MZ requests additional stack memory
        ; Pinned FreeDOS ChildEnv: ceil((2 + ENV_KEEPFREE=83)/16) = 6.
        ; COM: 6 env + 1 split MCB + 16 PSP + 8 image/stack = 31.
        ; MZ: 6 + 1 + 16 PSP + (1*32 - 4 header) + 32 minalloc = 83.
        ; The pinned MZ loader reserves the whole last file page. Preserve
        ; that FreeDOS behavior; do not substitute a compact-image formula.
        cmp word [com_min], 31
        jne fail
        cmp word [mz_min], 83
        jne fail
        mov word [stage], 8
        mov dx, repetition_text
        mov ah, 09h
        int 21h
        mov word [rounds], 32
.repeat:
        mov dx, com_name
        call execute
        cmp al, 1
        jne fail
        mov dx, mz_name
        call execute
        cmp al, 1
        jne fail
        dec word [rounds]
        jnz .repeat
        mov word [stage], 9           ; release only our own guard allocations
        xor si, si
.release:
        mov es, [blocks + si]
        mov ah, 49h
        int 21h
        jc fail
        add si, 2
        dec word [count]
        jnz .release
        mov word [stage], 10
        call largest
        cmp bx, [baseline]
        jne fail
        call restore_strategy
        jc fail
        mov dx, com_text
        mov ah, 09h
        int 21h
        mov bx, [com_min]
        call hex_word
        mov dx, mz_text
        mov ah, 09h
        int 21h
        mov bx, [mz_min]
        call hex_word
        mov dx, passed
        mov ah, 09h
        int 21h
        mov ax, 4c00h
        int 21h

; Return AL=1 only for child exit 42/type 0; AL=0 only for DOS error 8.
; The child parameter block supplies an explicit empty environment and tail.
; Check the capacity and live guards after EVERY successful or failed EXEC.
execute:
        push cs
        pop es
        mov bx, parameters
        mov ax, 4b00h
        int 21h
        push cs
        pop ds
        push cs
        pop es
        jnc .ran
        cmp ax, 8
        jne fail
        mov byte [outcome], 0
        jmp .check
.ran:
        mov ah, 4dh
        int 21h
        cmp ax, 002ah
        jne fail
        mov byte [outcome], 1
.check:
        call largest
        cmp bx, [budget]
        jne fail
        xor si, si
        mov cx, [count]
.guard:
        mov ax, [blocks + si]
        mov es, ax
        cmp word [es:0], 0a55ah
        jne fail
        dec ax
        mov es, ax
        mov ax, cs
        cmp [es:1], ax
        jne fail
        add si, 2
        loop .guard
        mov al, [outcome]
        ret

largest:
        mov bx, 0ffffh
        mov ah, 48h
        int 21h
        jnc fail
        cmp ax, 8
        jne fail
        ret
restore_strategy:
        cmp byte [have_strategy], 0
        je .done
        mov ax, 5801h
        mov bx, [strategy]
        int 21h
.done:
        ret
fail:
        push cs
        pop ds
        call restore_strategy
        mov dx, failed
        mov ah, 09h
        int 21h
        mov bx, [stage]
        call hex_word
        mov dx, newline
        mov ah, 09h
        int 21h
        mov ax, 4c01h                  ; normal DOS termination reclaims guards
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

com_name db 'CHILD.COM',0
mz_name db 'CHILD.EXE',0
exhaustion_text db 'EXEC: exhaustion checks',13,10,'$'
boundary_text db 'EXEC: scanning tail (hex paragraphs): $'
repetition_text db 'EXEC: boundary found; running 32 COM/MZ pairs',13,10,'$'
com_text db 'EXEC COM minimum free tail (hex paragraphs): $'
mz_text db 13,10,'EXEC MZ minimum free tail (hex paragraphs): $'
passed db 13,10,'EXEC: PASS (32 COM/MZ pairs; exhaustion rejection; capacity restored)',13,10,'$'
failed db 'EXEC: FAIL stage $'
newline db 13,10,'$'
align 2, db 0
parameters dw 0, command_tail, 0, 5ch, 0, 6ch, 0
command_tail db 0,13
stage dw 1
strategy dw 0
baseline dw 0
budget dw 0
com_min dw 0
mz_min dw 0
rounds dw 0
count dw 0
blocks times 32 dw 0
have_strategy db 0
outcome db 0
align 16, db 0
empty_environment db 0, 0
align 2, db 0
        times 512 db 0
stack_top:
