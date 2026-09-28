# M16 DOS console input and cursor contract

Status: implemented in the M16 candidate; guest qualification remains pending.
The raw M11 matrix entry and its early diagnostic ABI remain intact. The M16
adapter is used only by the DOS CON character-device path.

## Input ownership and byte contract

The PC-88VA kernel owns one read-only poll of the fifteen active-low matrix
rows per DOS input request. Physical coordinates and printable ASCII follow the
M11 source map in
[`m11-console-input-adr.md`](m11-console-input-adr.md), based on VAEG's
`io/serial.c` and `sdl2/kbdpaste.c`. The adapter does not call a keyboard BIOS
routine, access IBM or NEC98 keyboard memory, or install an interrupt handler.

The DOS adapter translates one unique make edge into a complete event in an
eight-entry ring. ASCII events are one byte. Extended events are stored as a
word whose low byte is `00h` and whose high byte is the second DOS byte. CON
status peeks the next byte without consuming it. CON reads consume the first
byte and retain an extended event's second byte until the next read. Input
flush clears queued events and any pending second byte, resets repeat state,
and makes the next matrix poll adopt held keys as the baseline. Unsupported
modes and ambiguous simultaneous makes produce no DOS character.

The physical mapping below is common to VA and VA2 because both use this
PC-88VA kernel matrix adapter. The DOS values are FreeDOS CON scan-code values;
they are not raw PC keyboard scan codes.

| Physical key | Matrix row / bit | DOS input | Repeat | Consumer |
| --- | --- | --- | --- | --- |
| Printable ASCII and Space | M11 map | ASCII byte | Yes, except control bytes | FreeDOS input / FreeCOM text insertion |
| Enter | row 14, bit 0 or 1 | `0Dh` | No | DOS command line |
| Backspace | row 12, bit 5 | `08h` | Yes | FreeCOM line editing |
| Up / Down / Left / Right | 8/1, 10/1, 10/2, 8/2 | `00h,48h` / `00h,50h` / `00h,4Bh` / `00h,4Dh` | Yes | History and cursor movement |
| Home / Help-End | 8/0, 10/3 | `00h,47h` / `00h,4Fh` | No | FreeCOM line editing |
| Insert / Delete | 12/6, 12/7 | `00h,52h` / `00h,53h` | No | FreeCOM insert mode / line editing |
| F1-F5 | row 9, bits 1-5 | `00h,3Bh`-`00h,3Fh` | No | FreeCOM F1/F3/F5 history actions; other keys are delivered to DOS |
| F6-F10 | row 12, bits 0-4 | `00h,40h`-`00h,44h` | No | Delivered to DOS; no extra shell action |
| Ctrl+Left / Ctrl+Right | Ctrl plus the corresponding arrow | `00h,73h` / `00h,74h` | No | FreeCOM word movement |
| Shift+F1-F10 | Shift plus F1-F10 | `00h,80h`-`00h,89h` | No | PC-88VA extension; no shell action |
| Shift+Up/Down/Left/Right | Shift plus the corresponding arrow | `00h,8Ah`-`00h,8Dh` | No | PC-88VA extension; no shell action |
| Ctrl+letter | Ctrl plus an alphabetic key | `01h`-`1Ah` | No | Common DOS control-key handling |
| Other modifier or mode combinations | Matrix state | No character | No | Ignored by DOS CON |

F1-F10 and the editing-key bytes above follow the selected common FreeDOS
CON/FreeCOM key contract. The shifted-key range is a PC-88VA adapter extension
to preserve the physical key event without assigning it an undocumented BIOS
scan code or a new shell shortcut. No F11, F12, Page Up or Page Down physical
keys are claimed.

## Repeat policy

Only the DOS matrix adapter produces repeats. A held printable key, Backspace
or unmodified arrow repeats after 30 observed M10 VRTC rising edges and then
every 4 observed edges. These units are M10 clock ticks, not milliseconds; M10
does not promise a calibrated wall-clock frequency. Each repeat is queued as a
whole event. If the queue is full, the repeat is dropped and its next deadline
is set from the current tick, so missed intervals never produce a burst.
Releasing the owning matrix key stops repeats; already queued input remains.
F-keys, Enter, modifiers, control characters and all other extended keys do
not repeat. DOS CON may enter with interrupts enabled, while the M10 VRTC
sampling service requires IF and DF clear. Repeat sampling brackets that
bounded service call with the required flags and restores the original caller
flags before returning.

The source-built DOS probe captures the normal AH=07h stream while the frontend
holds keys without synthesizing repeat events: one short `q`, `a` held for 90
guest frames, a 120-frame release interval, one short `c`, then `b` held for 38
guest frames. At the selected 30-edge delay and 4-edge period, the expected
capture is one `q`, 16 `a` events, one `c`, and three `b` events. The exact
byte fixture is `tests/m16/dos_repeat_sequence.json`; run it in paced and
accelerated VAEG sessions on both VA and VA2.

## Cursor ownership

The existing M09 Text BIOS remains the owner of text output, wrapping and
scrolling. FreeCOM reads the native text cursor through Text BIOS `INT 83h`,
`AH=2Eh`; it sets the zero-based cursor coordinates through `AH=08h` with
`DH=column`, `DL=row`. FreeCOM's editor-facing coordinates are one-based. The
editor sets a visible blinking line cursor in insert mode (`AH=25h, AL=13h`)
and a visible blinking block cursor in overwrite mode (`AH=25h, AL=03h`).
These calls stay in the `PC88VA` target branch; IBM `INT 10h`, NEC98 `INT 18h`
and direct text-memory cursor state are not used.

## Verification boundary

The fdkernel ROM-free tests assemble and execute the production matrix and DOS
adapter code. The M16 clean build selects FreeCOM's `pc88va` target and enables
its enhanced line editor. Static source checks bind the target to DOS
`INT 21h/AH=07h`, common extended-key constants and the native cursor calls.
These checks do not establish actual VA or VA2 keyboard delivery, visible
cursor placement, or shell-history behavior; those require the separate guest
qualification on each model.

The editing-repeat workload is `tests/m16/dos_repeat_editing.script`, using
that same bounded DOS probe. It holds Backspace and Left for 90 guest frames
and Right for 38, separated by release intervals. The expected byte fixture
keeps every repeated extended key as a complete zero-prefix/second-byte pair.
Qualification must record VA and VA2 at paced and accelerated settings;
source-level fixture checks alone are not guest acceptance.
