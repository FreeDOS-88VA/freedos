# MS-DOS 4 COMMAND on the PC-88VA FreeDOS kernel (experimental)

This is a separate shell compatibility experiment, not a change to the normal
FreeCOM distribution or an MS-DOS kernel port. The Microsoft component source
stays in its own fork, not in the parent. Pins and provenance are in
`config/m19/msdos4-research.json`. Microsoft sources and bundled original DOS
build tools are MIT-licensed; emu2 is GPL-2.0. No proprietary ROM/media is needed
to build. VAEG verification is separate and requires the owner's private setup.

## Rebuild from public sources

On Linux/x86_64 install Python 3.12+, Git, a C compiler and Make, and follow
`tools/m19/README.md` to prepare the pinned normal M19 toolchain. Clone these
external component repositories (not copies of their source files in this
parent):

```
git clone https://github.com/nakatamaho/MS-DOS.git /path/to/MS-DOS
git clone https://github.com/dmsc/emu2.git /path/to/emu2
```

From a clean committed parent checkout:

```
python3 -B tools/m19/qa/msdos4_media.py \
  --msdos-repo /path/to/MS-DOS --emu2-repo /path/to/emu2 \
  --output build/m19-msdos4-qa-NEW
```

Use a new output directory each time. The command verifies source archive
identities, rebuilds the entire normal M19 disk twice in isolated containers,
validates its public instance, builds emu2 freshly from its pinned source for
each shell build, generates message indexes/classes with original BUILDIDX and
BUILDMSG, assembles with original MASM 5.10, links with LINK 3.65 and converts
with EXE2BIN. All original tools come from the pinned public Microsoft tree.
No old candidate, saved COMMAND.COM or saved message classes are inputs.
The two QA compositions must have identical bytes and independent readback.

The resulting `MSDOS4-QA.D88` has `SHELL=A:\COMMAND.COM A:\ /P`, a small
AUTOEXEC.BAT setting PATH/PROMPT, the Microsoft license, and the newly rebuilt
M19 programs. It does not change the normal disk in `dist/m19`. The kernel,
loader and placement contract are unchanged and are reverified by the complete
build. Do not use SYS to transfer this shell as a qualified configuration.

For an isolated shell build, use `build_msdos4.py --msdos-repo ... --emu2-repo
... --output ...`. By default it builds the unmodified Microsoft base. Pass
`--msdos-revision` with the full fork commit from the lock and `--profile
pc88va` for the adapted shell. `--profile original` on that fork must reproduce
the original binary; `--profile freedos` keeps IBM console CLS for PC testing.

## Adaptations and boundaries

- `/DFREEDOS`: use FreeDOS's native DOS version/OEM identity; do not globally
  spoof VERSION=4.00. Skip unsupported OS/2 extended attributes in COPY/TYPE;
  ordinary I/O and timestamp error handling remain intact.
- `/DPC88VA`: CLS uses the native text BIOS for standard CON, avoiding IBM
  INT 10h and the DOS adapter's control-byte filter. Redirected CLS writes the
  ANSI clear/home bytes through DOS file I/O instead. A missing BIOS vector
  is rejected without calling it.
- Standard MS-DOS 4 parsing, transient reload, batch and environment behavior
  are not replaced. Set PATH in AUTOEXEC.BAT rather than expecting CONFIG's
  environment to be retained by the original shell initialization.
- `%NAME%` environment expansion is implemented in the original batch reader,
  not the interactive prompt. CALL does not propagate an outer redirection to
  every command of the called batch. These historical parsing rules are kept;
  `MS4QA.BAT` puts each redirection on the command being measured. Use
  `COMMAND /C ...`, not interactive `%COMSPEC% /C ...`.
- Default builds without the definitions retain the original code paths.
  This does not make any MS-DOS binary a general FreeDOS compatibility target.

## Guest checks

On disposable copies test startup, VER, CLS, DIR, COPY/TYPE/REN/DEL, missing
file errors, redirection and pipelines, SET expansion, batch CALL/FOR/IF and
ERRORLEVEL. Run MEMMAP /CHECK before/after and exercise repeated COM/MZ EXEC
and transient reload, including JWASMR builds/runs of HELLO and MZDEMO.
Read guest-written files back after stopping the emulator; screenshots alone
are not content validation. Record the exact disk/emulator identities and
installed versus retained RAM separately in excluded evidence. Do not infer
VA, VA2, smaller-memory or stale-setting coverage from another configuration.

Inject `config/m19/msdos4-guest-input.txt` with the owner's emulator adapter.
After stopping the guest, run `python3 -B tools/m19/qa/msdos4_readback.py
--baseline build/m19-msdos4-qa-NEW/MSDOS4-QA.D88 --guest PRIVATE-COPY.d88
--output PRIVATE-RESULT.json`. Output must be outside tracked source paths.
The synthetic negative tests reject missing outputs, payload drift, a spoofed
DOS version, failed MCB checks and absent COM/MZ execution evidence.

See `docs/porting/m19-report.md` for actual executed versus unrun coverage.
