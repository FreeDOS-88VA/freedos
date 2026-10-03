# Experimental repaired KSSF/COMMAND on PC-88VA

This branch is separate from the normal FreeCOM release and the published
MS-DOS 4 COMMAND Preview 1. The child `experiment/m19-kswap-va` enables the
existing VA kernel-swap feature on top of the independently qualified common
repair. Pair KSSF and COMMAND from the same full clean build: context layouts
are generated together. XMS remains disabled. No new kernel behavior is added.

## Complete public build

On Linux/x86_64 prepare the identity-pinned toolchain using `tools/m19/README.md`
and `make m19-toolchain`. From a clean, committed checkout with pinned submodules:

```
python3 -B tools/m19/qa/kswap_media.py --output build/NEW
```

This rebuilds the entire kernel/loader, shell, support applications and source
bundle twice, verifies the normal public instance and linked placement/carrier,
assembles KSSF and component-owned regression fixtures, and composes two
independent QA disks for each `/E:512` and `/E:8192` case. No old disk or saved
DOS executable is a build input. The normal source-generated image includes
the pair but does not configure the wrapper; the separate QA compositions
add `SHELL=A:\KSSF.COM A:\COMMAND.COM /E:SIZE /P`, a minimal AUTOEXEC and the
freshly assembled probes. Final disks and guest results stay Git-excluded.

## Separate guest qualification

Use fresh writable copies. Record exact parent/component/disk/emulator
identities and installed RAM versus persisted selection independently in
excluded evidence. First exercise VA2/640 KiB; after success, exercise VA and
the 512-KiB installed/640-KiB retained regression. Confirm startup visually
without early input, then run `config/m19/kswap-guest-input.txt` using the
owner's separately maintained emulator input adapter. Do not modify emulator
source here. Keep visual capture separate from the full automated workflow.
Require a completed input sequence, final shell prompt and settled disk I/O.

```
python3 -B tools/m19/qa/kswap_readback.py \
  --baseline build/NEW/KSWAP-E512.D88 --guest PRIVATE-COPY.d88 \
  --output PRIVATE-RESULT.json
```

The inspector requires an ordinary child with live COMMAND owners, a larger
swapped allocation with none, twenty identical consecutive swapped results,
preserved environment/alias/history/tail, relocated swapped MZ exit status 7,
fresh guest COM/MZ assembly/execution, stable MCB accounting and original
payload preservation. Host negatives reject absent outputs and false success.
The probe/accounting algorithm is maintained locally from the independent
component verifier at `f5512b5a1756768830b541a274ac48973c46de12`; its PC
acceptance state is not inherited as VA evidence.

Batch, pipes and redirection of the swapped command remain unsupported.
This workflow does not qualify secondary-shell swapping, UMB, live environment
relocation, failed-reload cleanup, OOM fallback on VA, Borland or hardware.
A source-built HOG fixture is retained outside the disk for later explicitly
scoped pressure tests, not silently counted as run. An unrun/failed case is
not PASS. No normal release replacement or milestone HANDOFF READY is implied.
