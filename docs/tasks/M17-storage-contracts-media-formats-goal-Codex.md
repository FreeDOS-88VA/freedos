# M17 storage contracts, media formats and kernel configuration

Start from parent `fc891f3cd424c281680dd15b3f269bef4a4d2880` on
`topic/m16-floppy-formats-console-input`. Preserve this checkpoint and its
component/media identities. M16 is partial, not accepted; independent M17 work
is authorized by the owner. Do not transfer historical acceptance.

The owner additionally requests restoring DOS CONFIG.SYS processing in M17.
The loader already reads PC88VA_LOADSEG; keep that early selector and run the
common kernel configuration passes afterward. Remove the M13 temporary skip,
correct VA-specific call/stack/memory integration, and qualify ordinary settings
and DEVICE= using actual guest execution. Preserve upstream DOS semantics.
Do not introduce a replacement DOS parser. Report unsupported platform-specific
settings explicitly. Keep the default ten-buffer disk cache and one-sector VA
transfer buffer unless overridden by supported DOS settings.

## Work

1. Audit actual DEVICE=/INIT/header/request/resident-end/DPB/unit registration.
2. Restore configuration and its required VA adapter boundaries. Verify missing
   configuration, normal configuration, FDCONFIG.SYS precedence, loader selector
   coexistence, positive/negative driver initialization and measured memory.
3. Define built-in FDD/SASI and external SCSI ownership, sector/capacity/partition/
   BPB/drive mapping and failures. Keep SCSI boot excluded and MO last.
4. Produce deterministic public FAT12/FAT16 data fixtures with milestone-local
   producers and independent inspectors. Reject malformed geometry, partition
   ranges, BPBs, FAT chains and identities. Fixture validity is not guest FAT16.
5. Clean-build the complete current guest distribution twice from committed
   exports, without historical milestone runtime directories; compare artifacts.
6. Record scoped HOST PASS and actual guest results separately. Commit/push
   components before parent gitlinks; qualify exact implementation and publication
   CI. Preserve private runtime evidence outside Git. Hardware is optional.
7. Hand off bounded SASI data-drive work to M18 and external SCSI work to M20.
   Do not implement operational SCSI or native HDD boot in M17.

The roadmap remains `docs/freedos-pc88va-milestones-M13-M31.md`. The current
memory rules in AGENTS.md apply, including INIT SS != DS, measured RAM,
consecutive low resident/work placement and temporary-release ownership.
