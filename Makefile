.DEFAULT_GOAL := help

.PHONY: help submodules component-status verify-scaffold m01-host-portability m01-image-identity m01-preflight m01-image m01-build m01-compare m01-enroll-golden m01-verify m01-clean m02-preflight m02-clean m02-bundle m02-compare m02-verify m02-enroll-golden m02 m03-preflight m03-clean m03-scan m03-compare m03-enroll-golden m03-verify m03 m04-preflight m04-private-evidence m04-verify m04 m04r1-license-verify m05-preflight m05-clean m05-build m05-compare m05-enroll-golden m05-negative-tests m05-verify m05 m06-preflight m06-prepare-m05 m06-clean m06-build m06-nec98-regression m06-media m06-compare m06-enroll-golden m06-negative-tests m06-verify m06 m07-preflight m07-clean m07-probe m07-variants m07-public-tests m07-public-verify m07-enroll-golden m07-redact m07-public m07r2-tests m07r2-verify m07r2-private-evidence m07r2-public m07r3-tests m07r3-verify m07r3-public m07r4-tests m07r4-verify m07r4-public m07r5-tests m07r5-verify m07r5-public m07r6-tests m07r6-verify m07r6-public m07-completion-tests m07-completion-verify m07-completion-public verify

M10_PYTHON ?= python3
.PHONY: m10-preflight m10-tests m10-build m10-compare m10-media m10-private-run m10-verify m10-accept m10 m11-preflight m11-build m11-compare m11-verify m11-accept m11 m12-preflight m12-build m12-compare m12-verify m12-accept m12 m13-preflight m13-build m13-compare m13-verify m13-accept m13
m10-preflight:
	@$(M10_PYTHON) -B tools/m10/preflight.py $(if $(M10_ACCEPTED_ROOT),--accepted-root "$(M10_ACCEPTED_ROOT)")

m10-tests:
	@$(M10_PYTHON) -B -m unittest discover -s tests/qa -p 'test_milestone_acceptance.py'
	@$(M10_PYTHON) -B -m unittest discover -s tests/m10 -p 'test_*.py'
	@$(M10_PYTHON) -B -m unittest discover -s components/fdkernel/pc88va/tests -p 'test_*.py'

m10-build:
	@test -n "$(M10_CHILD_SHA)" -a -n "$(M10_COMMAND)" -a -n "$(M10_COUNTRY)" || { echo 'M10_CHILD_SHA, M10_COMMAND and M10_COUNTRY are required'; exit 2; }
	@bash tools/m10/compare_public_builds.sh "$(M10_CHILD_SHA)" "$(M10_COMMAND)" "$(M10_COUNTRY)"

m10-media:
	@test -n "$(M10_BUILD_ROOT)" || { echo 'M10_BUILD_ROOT is required'; exit 2; }
	@$(M10_PYTHON) -B tools/m10/build_controls.py "$(M10_BUILD_ROOT)" --output "$(M10_BUILD_ROOT)/fatal-controls.json"

m10-compare:
	@test -n "$(M10_BUILD_ROOT)" || { echo 'M10_BUILD_ROOT is required'; exit 2; }
	@$(M10_PYTHON) -B tools/m10/verify_m10.py --build-root "$(M10_BUILD_ROOT)"

m10-verify:
	@$(M10_PYTHON) -B tools/m10/verify_m10.py

m10-private-run:
	@$(M10_PYTHON) -B tools/m10/private_run.py

m10-accept:
	@test -n "$(M10_BUILD_ROOT)" || { echo 'M10_BUILD_ROOT is required'; exit 2; }
	@$(M10_PYTHON) -B tools/m10/verify_m10.py --accept --build-root "$(M10_BUILD_ROOT)"

m10: m10-accept

M11_PYTHON ?= python3
M11_CHILD_SHA ?= b08ace36670a05992d8ddaa4279727d9b17bd11e
M11_COMMAND ?= $(CURDIR)/build/payload/COMMAND.COM
M11_COUNTRY ?= $(CURDIR)/build/payload/COUNTRY.SYS
M11_BUILD_ROOT ?=
m11-preflight:
	@$(M11_PYTHON) -B tools/m11/preflight.py
m11-build:
	@test -f "$(M11_COMMAND)" -a -f "$(M11_COUNTRY)" || { echo 'M11_COMMAND and M11_COUNTRY are required'; exit 2; }
	@bash tools/m11/compare_public_builds.sh "$(M11_CHILD_SHA)" "$(M11_COMMAND)" "$(M11_COUNTRY)"
m11-compare:
	@test -n "$(M11_BUILD_ROOT)" || { echo 'M11_BUILD_ROOT is required'; exit 2; }
	@$(M11_PYTHON) -B tools/m11/verify_m11.py --build-root "$(M11_BUILD_ROOT)"
m11-verify:
	@$(M11_PYTHON) -B tools/m11/verify_m11.py
m11-accept:
	@test -n "$(M11_BUILD_ROOT)" || { echo 'M11_BUILD_ROOT is required'; exit 2; }
	@$(M11_PYTHON) -B tools/m11/verify_m11.py --accept --build-root "$(M11_BUILD_ROOT)"
m11: m11-accept

M12_PYTHON ?= python3
M12_CHILD_SHA ?= 21d9f3450276d42e5fedd1ddb9e80485b888cc07
M12_COMMAND ?= $(CURDIR)/build/payload/COMMAND.COM
M12_COUNTRY ?= $(CURDIR)/build/payload/COUNTRY.SYS
M12_BUILD_ROOT ?=
m12-preflight:
	@$(M12_PYTHON) -B tools/m12/preflight.py
	@$(M12_PYTHON) -B tools/m12/verify_m12.py
m12-build:
	@test -f "$(M12_COMMAND)" -a -f "$(M12_COUNTRY)" || { echo 'M12_COMMAND and M12_COUNTRY are required'; exit 2; }
	@bash tools/m12/compare_public_builds.sh "$(M12_CHILD_SHA)" "$(M12_COMMAND)" "$(M12_COUNTRY)"
m12-compare:
	@test -n "$(M12_BUILD_ROOT)" || { echo 'M12_BUILD_ROOT is required'; exit 2; }
	@$(M12_PYTHON) -B tools/m12/verify_m12.py --build-root "$(M12_BUILD_ROOT)"
m12-verify:
	@$(M12_PYTHON) -B tools/m12/verify_m12.py
m12-accept: m12-compare m12-verify
m12: m12-accept

M13_PYTHON ?= python3
M13_CHILD_SHA ?= e432296345f1ccc783a42c02baa7ffe4bd2a6eb8
M13_BUILD_ROOT ?=
m13-preflight:
	@$(M13_PYTHON) -B tools/m13/preflight.py
	@$(M13_PYTHON) -B tools/m13/verify_m13.py
m13-build:
	@bash tools/m13/compare_public_builds.sh "$(M13_CHILD_SHA)"
m13-compare:
	@test -n "$(M13_BUILD_ROOT)" || { echo 'M13_BUILD_ROOT is required'; exit 2; }
	@$(M13_PYTHON) -B tools/m13/verify_m13.py --build-root "$(M13_BUILD_ROOT)"
m13-verify:
	@$(M13_PYTHON) -B tools/m13/verify_m13.py
m13-accept:
	@test -n "$(M13_BUILD_ROOT)" || { echo 'M13_BUILD_ROOT is required'; exit 2; }
	@$(M13_PYTHON) -B tools/m13/verify_m13.py --accept --build-root "$(M13_BUILD_ROOT)"
m13: m13-accept

.PHONY: m14-preflight m14-verify m14-build m14-compare m14-tests m14-historical m14-accept
.PHONY: m15-loader-build m15-r7-rebuild
m14-preflight:
	@python3 -B tools/m14/preflight.py --output "$(M14_PREFLIGHT_ROOT)"
m14-verify:
	@python3 -B tools/m14/verify_m14.py
m14-build:
	@python3 -B tools/m14/build_public.py --output "$(M14_BUILD_ROOT)"
m14-compare:
	@python3 -B tools/m14/verify_m14.py --build-root "$(M14_BUILD_ROOT)"
m14-tests:
	@python3 -B tools/m14/run_tests.py
m14-historical:
	@python3 -B tools/m14/historical_regression.py --output "$(M14_HISTORICAL_ROOT)"
m14-accept:
	@python3 -B tools/m14/verify_m14.py --accept --build-root "$(M14_BUILD_ROOT)"

M15_PYTHON ?= /opt/local/bin/python3.12
M15_LOADER_OVERLAY ?=
M15_LOADER_OUTPUT ?=
M15_LOADER_REFERENCE ?=
M15_LOADER_EXTENT ?=
M15_BOOT_REFERENCE ?=
m15-loader-build:
	@test -n "$(M15_LOADER_OVERLAY)" -a -n "$(M15_LOADER_OUTPUT)" || { echo 'M15_LOADER_OVERLAY and M15_LOADER_OUTPUT are required'; exit 2; }
	@PYTHONDONTWRITEBYTECODE=1 $(M15_PYTHON) -B tools/m15/build_loader_pair.py --overlay "$(M15_LOADER_OVERLAY)" --output "$(M15_LOADER_OUTPUT)" $(if $(M15_LOADER_REFERENCE),--expected-loader "$(M15_LOADER_REFERENCE)") $(if $(M15_LOADER_EXTENT),--stage1-extent "$(M15_LOADER_EXTENT)") $(if $(M15_BOOT_REFERENCE),--expected-stage1 "$(M15_BOOT_REFERENCE)")

M15_R7_SEED ?=
.PHONY: m15-image m15-toolchain
M15_IMAGE_OUTPUT ?= build/m15-image
M15_IMAGE_TOOLCHAIN ?= freedos-pc88va-m01:local
m15-toolchain:
	@PYTHONDONTWRITEBYTECODE=1 $(M15_PYTHON) -B tools/m15/toolchain.py --image "$(M15_IMAGE_TOOLCHAIN)"

m15-image:
	@PYTHONDONTWRITEBYTECODE=1 $(M15_PYTHON) -B tools/m15/build_image.py --output "$(M15_IMAGE_OUTPUT)" --image "$(M15_IMAGE_TOOLCHAIN)"

M15_R7_PROFILE ?=
M15_R7_OUTPUT ?=
m15-r7-rebuild:
	@test -n "$(M15_R7_SEED)" -a -n "$(M15_R7_PROFILE)" -a -n "$(M15_R7_OUTPUT)" || { echo 'M15_R7_SEED, M15_R7_PROFILE and M15_R7_OUTPUT are required'; exit 2; }
	@PYTHONDONTWRITEBYTECODE=1 $(M15_PYTHON) -B tools/m15/rebuild_r7.py --seed "$(M15_R7_SEED)" --profile "$(M15_R7_PROFILE)" --output "$(M15_R7_OUTPUT)"

help:
	@printf '%s\n' \
		'Available targets:' \
		'  m10-preflight     Verify the exact M09 public handoff and CI identities' \
		'  m10-build         Build two isolated M10 source exports' \
		'  m10-media         Generate both public fatal selector controls' \
		'  m10-compare       Validate actual build records and golden identities' \
		'  m10-private-run   Invoke an explicit digest-bound local private runner' \
		'  m10-verify        Validate closed public schemas, instances and sources' \
		'  m10-accept        Run shared acceptance including historical regression' \
		'  m11-preflight     Verify exact M10 handoff before M11' \
		'  m11-build         Build two isolated M11 source exports' \
		'  m11-compare       Validate actual M11 build records and artifacts' \
		'  m11-verify        Validate M11 schemas, bindings and component identities' \
		'  m11-accept        Run the enforced M11 public acceptance gate' \
		'  m12-preflight     Verify the exact M11 handoff and M12 source identities' \
		'  m12-build         Build two isolated M12 source exports and fixture media' \
		'  m12-compare       Validate the M12 build pair against its manifest' \
		'  m12-verify        Validate M12 schemas, bindings and resident source' \
		'  m12-accept        Run the enforced M12 public acceptance gate' \
		'  m13-preflight     Verify the exact M12 handoff and M13 source identities' \
		'  m13-build         Build two isolated M13 common-core source exports' \
		'  m13-compare       Validate the M13 build pair and artifact bindings' \
		'  m13-verify        Validate M13 schemas, instances and component identities' \
		'  m13-accept        Run the enforced M13 public acceptance gate' \
		'  m15-loader-build  Build a loader twice from one explicit overlay and bind its inputs' \
		'  m15-image         Build complete media twice from public source inputs' \
		'  m15-toolchain     Prepare or verify the pinned M15 build environment' \
		'  m18-toolchain     Prepare or verify the pinned M18 Linux/amd64 environment' \
		'  m18-disk          Build and compare two isolated M18 native 2HD disks' \
		'  m18-accept        Verify the M18 distribution instance and source bindings' \
		'  m18-clean         Remove only marked M18 intermediate build output' \
		'  help              Show this help' \
		'  submodules        Initialize/update locked submodules' \
		'  component-status  Show submodule status' \
		'  verify-scaffold   Validate the M00 scaffold' \
		'  m01-host-portability  Run host portability regression checks' \
		'  m01-image-identity  Run image identity and cleanup checks' \
		'  m01-preflight     Check the read-only M01 host prerequisites' \
		'  m01-image         Build the pinned M01 toolchain image' \
		'  m01-build         Perform two isolated M01 baseline builds' \
		'  m01-compare       Compare the two M01 build runs' \
		'  m01-enroll-golden Explicitly enroll a passing M01 comparison as golden' \
		'  m01-verify        Run offline M01 verification' \
		'  m01-clean         Remove only ignored M01 build results' \
		'  m02-preflight     Check M02 identity, host, and verified M01 inputs' \
		'  m02-clean         Remove only generated M02 result paths' \
		'  m02-bundle        Assemble independent M02 bundle runs' \
		'  m02-compare       Compare M02 trees, tar archives, and sidecars' \
		'  m02-verify        Verify M02 against its committed golden' \
		'  m02-enroll-golden Enroll an M02 golden after a passing comparison' \
		'  m02               Run the complete non-destructive M02 sequence' \
		'  m03-preflight     Check M03 baseline and component identity' \
		'  m03-clean         Remove only generated M03 result paths' \
		'  m03-scan          Generate two deterministic M03 source censuses' \
		'  m03-compare       Compare the two M03 census outputs' \
		'  m03-enroll-golden Enroll an M03 golden after a passing comparison' \
		'  m03-verify        Verify M03 against its reviewed golden' \
		'  m03               Run the complete non-destructive M03 sequence' \
		'  m04-preflight     Verify the accepted public M04 identity' \
		'  m04-private-evidence  Validate local M04 TXT/Markdown locators' \
		'  m04-verify        Verify the public provisional M04 contract' \
		'  m04               Run the public non-destructive M04 verification' \
		'  m04r1-license-verify  Verify the GPL-2.0-or-later root policy' \
		'  m05-preflight     Verify M05 identities and accepted M02 inputs' \
		'  m05-clean         Remove only generated M05 result paths' \
		'  m05-build         Build and inspect two independent M05 media runs' \
		'  m05-compare       Compare complete M05 result trees byte-for-byte' \
		'  m05-enroll-golden Explicitly enroll a passing M05 textual golden' \
		'  m05-negative-tests  Run M05 fail-closed media tests' \
		'  m05-verify        Verify M05 runs against the committed golden' \
		'  m05               Run the complete deterministic M05 sequence' \
		'  m06-preflight     Verify M06 child, historical identities, M05 bytes, and toolchain' \
		'  m06-prepare-m05   Regenerate accepted M05 prerequisites under the M06 gitlink overlay' \
		'  m06-clean         Remove only generated M06 result paths' \
		'  m06-build         Build two PC-88VA targets and two NEC98 regressions' \
		'  m06-nec98-regression  Verify all accepted fdkernel NEC98 artifact hashes' \
		'  m06-media         Build and inspect two derived compile-only media runs' \
		'  m06-compare       Compare complete M06 result trees byte-for-byte' \
		'  m06-enroll-golden Explicitly enroll a passing M06 textual golden' \
		'  m06-negative-tests  Run M06 fail-closed parent tests' \
		'  m06-verify        Verify M06 runs against the committed golden' \
		'  m06               Run the complete deterministic M06 sequence' \
		'  m07-preflight     Verify accepted identities and public M07 inputs' \
		'  m07-clean         Remove only generated public M07 result paths' \
		'  m07-probe         Build the probe and five variants twice' \
		'  m07-variants      Compare complete public result trees' \
		'  m07-public-tests  Run M07 ROM-free fail-closed tests' \
		'  m07-public-verify Verify public results against the M07 golden' \
		'  m07-public        Run the complete ROM-free M07 public gate' \
		'  m07r2-tests       Run synthetic D88 and abstract-boundary tests' \
		'  m07r2-verify      Verify the redacted M07R2 Class A status' \
		'  m07r2-private-evidence  Check ignored local CONTROL evidence without printing values' \
		'  m07r2-public      Run the complete ROM-free M07R2 public gate' \
		'  m07r3-tests       Run M07R3 public abstract-status tests' \
		'  m07r3-verify      Verify the M07R3 public diagnosis record' \
		'  m07r3-public      Run the ROM-free M07R3 public gate' \
		'  m07r4-tests       Run M07R4 public reconstruction-status tests' \
		'  m07r4-verify      Verify the M07R4 abstract B2 reconstruction record' \
		'  m07r4-public      Run the ROM-free M07R4 public gate' \
		'  m07r5-tests       Run M07R5 abstract request-gate tests' \
		'  m07r5-verify      Verify the M07R5 abstract request-gate record' \
		'  m07r5-public      Run the ROM-free M07R5 public gate' \
		'  m07r6-tests       Run M07R6 subsystem command-gate tests' \
		'  m07r6-verify      Verify the M07R6 abstract command-gate record' \
		'  m07r6-public      Run the ROM-free M07R6 public gate' \
		'  m07-completion-tests  Run privacy-safe M07 completion tests' \
		'  m07-completion-verify Verify the final M07 completion record' \
		'  m07-completion-public Run the final ROM-free M07 completion gate' \
		'  m09-tests         Run ROM-free early-console and privacy tests' \
		'  m09-public-verify Verify bound early-console acceptance records' \
		'  m09-public        Run public M09 gates; never execute private trials' \
		'  verify            Run scaffold and available M01 verification'

submodules:
	@git submodule update --init --recursive

component-status:
	@git submodule status --recursive

verify-scaffold:
	@python3 tools/verify_scaffold.py

m01-host-portability:
	@bash tools/m01/test_host_portability.sh

m01-image-identity:
	@python3 tools/m01/test_image_identity.py

m01-preflight:
	@bash tools/m01/build_baseline.sh preflight

m01-image:
	@bash tools/m01/build_baseline.sh image

m01-build:
	@bash tools/m01/build_baseline.sh build

m01-compare:
	@bash tools/m01/build_baseline.sh compare

m01-enroll-golden:
	@bash tools/m01/build_baseline.sh enroll

m01-verify:
	@bash tools/m01/build_baseline.sh verify

m01-clean:
	@bash tools/m01/build_baseline.sh clean

m02-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/assemble_bundle.py --preflight

m02-clean:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/assemble_bundle.py --clean

m02-bundle:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/assemble_bundle.py --bundle

m02-compare:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/compare_bundles.py

m02-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/verify_bundle.py

m02-enroll-golden:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m02/verify_bundle.py --enroll-golden --supersede-golden

m02:
	@$(MAKE) m02-preflight
	@$(MAKE) m02-clean
	@$(MAKE) m02-bundle
	@$(MAKE) m02-compare
	@$(MAKE) m02-verify

m03-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/verify_m03.py --baseline

m03-clean:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/verify_m03.py --clean

m03-scan:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/scan_port_surface.py --repo-root . --output qa/results/m03/run-1/port-surface.json
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/scan_port_surface.py --repo-root . --output qa/results/m03/run-2/port-surface.json

m03-compare:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/verify_m03.py --compare

m03-enroll-golden:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/verify_m03.py --enroll-golden --supersede-golden

m03-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m03/verify_m03.py --verify

m03:
	@$(MAKE) m03-preflight
	@$(MAKE) m03-clean
	@$(MAKE) m03-scan
	@$(MAKE) m03-compare
	@$(MAKE) m03-verify

m04-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m04/verify_m04.py --verify

m04-private-evidence:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m04/verify_m04.py --private-evidence

m04-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m04/verify_m04.py --verify

m04:
	@$(MAKE) m04-verify

m04r1-license-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/qa/verify_license_policy.py

m05-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/verify_m05.py --preflight

m05-clean:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/verify_m05.py --clean

m05-build:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/build_media.py --repo-root . --output qa/results/m05/run-1
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/inspect_media.py --repo-root . --run-dir qa/results/m05/run-1
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/build_media.py --repo-root . --output qa/results/m05/run-2
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/inspect_media.py --repo-root . --run-dir qa/results/m05/run-2

m05-compare:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/compare_media.py

m05-enroll-golden:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/verify_m05.py --enroll-golden

m05-negative-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/m05 -p 'test_*.py'

m05-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m05/verify_m05.py --verify

m05:
	@$(MAKE) m05-preflight
	@$(MAKE) m05-clean
	@$(MAKE) m05-build
	@$(MAKE) m05-compare
	@$(MAKE) m05-negative-tests
	@$(MAKE) m05-verify

m06-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --preflight

m06-prepare-m05:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --prepare-m05

m06-clean:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --clean

m06-build:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --build

m06-nec98-regression:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --nec98-regression

m06-media:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --media

m06-compare:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --compare

m06-enroll-golden:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --enroll-golden

m06-negative-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --negative-tests

m06-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m06/m06.py --verify

m06:
	@$(MAKE) m06-preflight
	@$(MAKE) m06-clean
	@$(MAKE) m06-build
	@$(MAKE) m06-nec98-regression
	@$(MAKE) m06-media
	@$(MAKE) m06-compare
	@$(MAKE) m06-negative-tests
	@$(MAKE) m06-verify

m07-preflight:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --preflight

m07-clean:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --clean

m07-probe:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --build

m07-variants:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --compare

m07-public-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --tests

m07-public-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --verify

m07-enroll-golden:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/m07.py --enroll-golden

m07-redact:
	@test -n "$(M07_PRIVATE_RESULT)" || { printf '%s\n' 'M07_PRIVATE_RESULT is required'; exit 2; }
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/redact_private_result.py --input "$(M07_PRIVATE_RESULT)" --output config/m07/public-result.json

m07-public:
	@$(MAKE) m07-preflight
	@$(MAKE) m07-clean
	@$(MAKE) m07-probe
	@$(MAKE) m07-variants
	@$(MAKE) m07-public-tests
	@$(MAKE) m07-public-verify

m07r2-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/m07r2 -p 'test_*.py'

m07r2-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07r2/verify_m07r2.py

m07r2-private-evidence:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07r2/verify_m07r2.py --private-evidence

m07r2-public:
	@$(MAKE) m07r2-tests
	@$(MAKE) m07r2-verify

m07r3-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/m07r3 -p 'test_*.py'

m07r3-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07r3/verify_m07r3.py

m07r3-public:
	@$(MAKE) m07r3-tests
	@$(MAKE) m07r3-verify

m07r4-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/m07/test_m07r4.py

m07r4-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/verify_m07r4.py

m07r4-public:
	@$(MAKE) m07r4-tests
	@$(MAKE) m07r4-verify

m07r5-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/m07/test_m07r5.py

m07r5-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/verify_m07r5.py

m07r5-public:
	@$(MAKE) m07r5-tests
	@$(MAKE) m07r5-verify

m07r6-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/m07/test_m07r6.py

m07r6-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/verify_m07r6.py

m07r6-public:
	@$(MAKE) m07r6-tests
	@$(MAKE) m07r6-verify

m07-completion-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/m07/test_m07_completion.py

m07-completion-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m07/verify_m07_completion.py

m07-completion-public:
	@$(MAKE) m07-completion-tests
	@$(MAKE) m07-completion-verify

.PHONY: m08-public-verify m08-tests

m08-public-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m08/verify_m08_public.py

m08-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s components/fdkernel/pc88va/tests -p 'test_m08_*.py'
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_m08_media.py tests/test_m08_acceptance.py

.PHONY: m09-tests m09-public-verify m09-public
m09-tests:
	@PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/m09 -p 'test_*.py'

m09-public-verify:
	@PYTHONDONTWRITEBYTECODE=1 python3 tools/m09/verify_m09.py

m09-public: m09-tests m09-public-verify

verify: verify-scaffold
	@if test -f qa/golden/m01-baseline.json && test -d qa/results/m01/run-1 && test -d qa/results/m01/run-2; then \
		bash tools/m01/build_baseline.sh verify; \
	else \
		printf '%s\n' 'M01 verification is not run: no generated two-run evidence is present.'; \
	fi

# M17 owns its complete build and media tooling.
.PHONY: m17-toolchain m17-build m17-fixtures
m17-toolchain:
	python3 -B tools/m17/toolchain.py
m17-build:
	python3 -B tools/m17/build_image.py --output $(if $(M17_OUTPUT),$(M17_OUTPUT),build/m17-image)
m17-fixtures:
	python3 -B tools/m17/produce.py --profiles config/m17/media-profiles.json --output $(if $(M17_FIXTURES),$(M17_FIXTURES),build/m17-storage)
	python3 -B tools/m17/inspect_storage.py --profiles config/m17/media-profiles.json --directory $(if $(M17_FIXTURES),$(M17_FIXTURES),build/m17-storage)

M18_PYTHON ?= python3
M18_IMAGE ?= freedos-pc88va-m18:local
M18_OUTPUT ?= build/m18
M18_DIST ?= dist/m18
M18_QA_OUTPUT ?= build/m18-allocator-qa
M18_WHEEL_CACHE ?= $(CURDIR)/build/m18-wheel-cache
.PHONY: m18-toolchain m18-disk m18-clean m18-host-tests m18-allocator-qa m18-accept
m18-toolchain:
	@PYTHONDONTWRITEBYTECODE=1 $(M18_PYTHON) -B tools/m18/toolchain.py --image "$(M18_IMAGE)"
m18-allocator-qa: m18-disk
	@PYTHONDONTWRITEBYTECODE=1 $(M18_PYTHON) -B tools/m18/build_allocator_qa.py --build "$(M18_OUTPUT)" --dist "$(M18_DIST)" --output "$(M18_QA_OUTPUT)"
m18-disk: m18-toolchain
	@M18_WHEEL_CACHE="$(M18_WHEEL_CACHE)" PYTHONDONTWRITEBYTECODE=1 $(M18_PYTHON) -B tools/m18/build_image.py --output "$(M18_OUTPUT)" --dist "$(M18_DIST)" --image "$(M18_IMAGE)"
m18-clean:
	@PYTHONDONTWRITEBYTECODE=1 $(M18_PYTHON) -B tools/m18/clean.py --path "$(M18_OUTPUT)"
m18-accept:
	@python3 -B tools/m18/verify_distribution.py --dist "$(M18_DIST)"
m18-host-tests:
	@M18_WHEEL_CACHE="$(M18_WHEEL_CACHE)" PYTHONDONTWRITEBYTECODE=1 $(M18_PYTHON) -B tools/m18/run_host_tests.py
