# M19 task: FORMAT cannot prepare blank media

Status: **IMPLEMENTED IN M19 (VAEG-validated; hardware NOT RUN)** — see `docs/porting/m19-report.md`. This records a known M18
limitation. It does not change the released M18 disk, its tooling or its
emulator-only validation scope.

## Observed behavior

The owner inserted a blank disk in B: in VAEG and ran `FORMAT B:` from the
released M18 disk. FORMAT refused the operation with:

```
FORMAT: B: lacks a valid native 2HD BPB; no write was attempted.
```

This is the designed M18 behavior, not a crash. The M18 FORMAT only writes
FAT12 metadata (FATs, root directory and boot record) on B: media that is
already sector-formatted and already has a valid native 2HD BPB. It never
formats tracks. A new or unformatted disk therefore cannot be prepared with
the M18 tools.

M18 VAEG FORMAT/CHKDSK/SYS results used disposable B: media generated on the
host by `tools/m18/qa/blank_data_media.py`, which already contains the BPB,
FATs and root directory. No M18 result covers a blank disk, and none should
be read as doing so.

## Missing function

The missing piece is track formatting of native 2HD media (80 cylinders, 2
heads, 8 sectors of 1024 bytes). This needs a platform adapter that calls the
PC-88VA BIOS disk-format service, plus a FORMAT path that uses it before the
existing metadata initialization. No milestone has implemented or qualified
such an adapter.

## Constraints

- Keep the adapter project-authored and public: a documented BIOS call
  interface, versioned in M19-local tooling/config/tests. Do not copy or
  derive values from ROM contents, private disks or traces.
- Follow the M19 milestone-local tooling rule; do not import from
  `tools/m18`, `config/m18` or `tests/m18` at runtime. Carry forward any
  needed M18 code as a maintained local copy with provenance.
- Keep FORMAT limited to B: and keep its explicit destructive confirmation.
  Fail closed on write protection, media change, unsupported geometry and
  BIOS errors, without leaving a half-written disk reported as success.
- Keep the selected FreeDOS behavior as the DOS baseline. Do not add
  unrelated DOS behavior to the kernel to support this tool.
- Update the on-disk README.TXT/QUICKSTR.TXT so users can see clearly whether
  new or unformatted media is supported.

## Required closure

- Host tests for the format adapter's request construction and error paths,
  plus the existing FAT12 metadata tests.
- A clean two-build public source build of the changed candidate.
- In VAEG, end-to-end on the exact candidate: a **blank** B: disk, then
  `FORMAT B:`, `CHKDSK B:`, `SYS A: B:`, then boot from the resulting disk
  and write/read back a guest file. Cover the affected VA/VA2 models and
  record write-protected and cancelled cases.
- Physical hardware remains optional. Without an actual hardware run, record
  it as NOT RUN or DEFERRED HARDWARE VALIDATION, never as HARDWARE PASS.
