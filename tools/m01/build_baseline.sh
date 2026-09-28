#!/usr/bin/env bash
set -eu

M01_SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
M01_ROOT=$(CDPATH= cd -- "$M01_SCRIPT_DIR/../.." && pwd)
M01_RESULTS_ROOT=$M01_ROOT/qa/results/m01
M01_RUNTIME_ROOT=$M01_RESULTS_ROOT/runtime
M01_SOURCE_ROOT=$M01_RESULTS_ROOT/source
M01_CONTRACT=$M01_ROOT/manifests/m01-build-contract.json
M01_TOOLCHAIN_LOCK=$M01_ROOT/manifests/toolchains.lock.json
M01_HOST_FS=$M01_ROOT/tools/m01/host_fs.py
M01_IMAGE_FILE=$M01_RUNTIME_ROOT/image.json
M01_BUILDX_CONFIG=${M01_ROOT}/qa/results/m01/buildx-config

read_toolchain_inputs() {
    while IFS="$(printf '\t')" read -r key value; do
        case "$key" in
            platform) M01_PLATFORM=$value ;;
            base_image) M01_BASE_IMAGE=$value ;;
            base_index_digest) M01_BASE_INDEX_DIGEST=$value ;;
            base_amd64_digest) M01_BASE_AMD64_DIGEST=$value ;;
            apt_snapshot) M01_APT_SNAPSHOT=$value ;;
            ow_release) M01_OW_RELEASE=$value ;;
            ow_release_tag) M01_OW_RELEASE_TAG=$value ;;
            ow_release_id) M01_OW_RELEASE_ID=$value ;;
            ow_tag_commit) M01_OW_TAG_COMMIT=$value ;;
            ow_package) M01_OW_PACKAGE=$value ;;
            ow_asset_id) M01_OW_ASSET_ID=$value ;;
            ow_package_size) M01_OW_PACKAGE_SIZE=$value ;;
            ow_publisher_md5) M01_OW_PUBLISHER_MD5=$value ;;
            ow_package_sha256) M01_OW_PACKAGE_SHA256=$value ;;
            ow_official_upstream_url) M01_OW_OFFICIAL_UPSTREAM_URL=$value ;;
            ow_official_github_url) M01_OW_OFFICIAL_GITHUB_URL=$value ;;
            ow_verification_method) M01_OW_VERIFICATION_METHOD=$value ;;
            ow_install_path) M01_OW_INSTALL_PATH=$value ;;
            ow_host_directory) M01_OW_HOST_DIRECTORY=$value ;;
        esac
    done < <(python3 - "$M01_TOOLCHAIN_LOCK" <<'PY'
import json
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
base = lock["canonical"]["base_image"]
apt = lock["canonical"]["apt"]
ow = lock["canonical"]["open_watcom"]
values = {
    "platform": lock["canonical"]["architecture"],
    "base_image": f"{base['repository']}:{base['tag']}",
    "base_index_digest": base["index_digest"],
    "base_amd64_digest": base["amd64_manifest_digest"],
    "apt_snapshot": apt["snapshot_id"],
    "ow_release": ow["release"],
    "ow_release_tag": ow["release_tag"],
    "ow_release_id": str(ow["release_id"]),
    "ow_tag_commit": ow["tag_commit"],
    "ow_package": ow["package"],
    "ow_asset_id": str(ow["asset_id"]),
    "ow_package_size": str(ow["asset_size"]),
    "ow_publisher_md5": ow["publisher_md5"],
    "ow_package_sha256": ow["sha256"],
    "ow_official_upstream_url": ow["official_upstream_url"],
    "ow_official_github_url": ow["official_github_url"],
    "ow_verification_method": ow["verification_method"],
    "ow_install_path": ow["install_path"],
    "ow_host_directory": ow["required_host_directory"],
}
for key, value in values.items():
    print(f"{key}\t{value}")
PY
    )
}

read_toolchain_inputs

cd "$M01_ROOT"
[ "$(basename -- "$M01_ROOT")" = freedos-pc88va ] || { printf '%s\n' 'error: wrong repository basename' >&2; exit 2; }
[ "$(git rev-parse --show-toplevel)" = "$M01_ROOT" ] || { printf '%s\n' 'error: command must run at repository root' >&2; exit 2; }
mkdir -p "$M01_BUILDX_CONFIG"
export BUILDX_CONFIG=$M01_BUILDX_CONFIG
M01_IMAGE_TAG=freedos-pc88va-m01:local
M01_FREECOM_TIMESTAMP=$M01_ROOT/config/m01/freecom-build-timestamp.json
IFS="$(printf '\t')" read -r M01_FREECOM_SOURCE_DATE_EPOCH M01_FREECOM_BUILD_DATE M01_FREECOM_BUILD_TIME < <(python3 "$M01_ROOT/tools/m01/freecom_timestamp.py" "$M01_FREECOM_TIMESTAMP")
IFS="$(printf '\t')" read -r M01_FDKERNEL_SOURCE_DATE_EPOCH M01_FDKERNEL_BUILD_DATE < <(python3 "$M01_ROOT/tools/m01/kernel_timestamp.py" "$M01_CONTRACT" components/fdkernel)

fail() {
    printf 'error: %s\n' "$*" >&2
    exit 1
}

portable_file_mode() {
    [ "$#" -eq 1 ] || fail "portable_file_mode expects exactly one path"
    python3 "$M01_HOST_FS" mode "$1"
}

portable_file_size() {
    [ "$#" -eq 1 ] || fail "portable_file_size expects exactly one path"
    python3 "$M01_HOST_FS" size "$1"
}

portable_file_hash() {
    [ "$#" -eq 2 ] || fail "portable_file_hash expects an algorithm and one path"
    case "$1" in
        md5|sha256) ;;
        *) fail "unsupported host hash algorithm: $1" ;;
    esac
    python3 "$M01_HOST_FS" "$1" "$2"
}

require_mode_0444() {
    [ "$#" -eq 1 ] || fail "require_mode_0444 expects exactly one path"
    local path=$1 mode
    mode=$(portable_file_mode "$path")
    case "$mode" in
        0[0-7][0-7][0-7]) ;;
        *) fail "invalid file mode for $path: $mode" ;;
    esac
    [ "$mode" = 0444 ] || fail "unexpected file mode for $path: $mode"
}

validate_gitlinks() {
    python3 - "$M01_ROOT" "$M01_CONTRACT" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
contract_path = Path(sys.argv[2])
sys.path.insert(0, str(root / "tools/qa"))
from current_components import CurrentComponentError, resolve_current_components
expected_paths = {
    "components/fdkernel",
    "components/freecom",
    "components/country",
}
expected_policy = {
    "components/fdkernel": {
        "name": "fdkernel",
        "repository": "https://github.com/nakatamaho/fdkernel.git",
        "branch": "nec98-current",
    },
    "components/freecom": {
        "name": "freecom",
        "repository": "https://github.com/nakatamaho/freecom_dbcs2.git",
        "branch": "deterministic-build-timestamp",
    },
    "components/country": {
        "name": "country",
        "repository": "https://github.com/FDOS/country.git",
        "branch": "master",
    },
}
lock_required = ("name", "path", "repository", "branch", "commit", "role", "stability")
contract_required = (
    "name", "path", "commit", "source_date_epoch", "working_directory",
    "build_commands", "required_artifacts", "upx_enabled",
)
full_commit = re.compile(r"[0-9a-f]{40}")


def validate_lock_schema(lock):
    if lock.get("schema_version") != 1 or lock.get("status") != "scaffold":
        raise SystemExit("components.lock.json schema or status is invalid")
    components = lock.get("components")
    if not isinstance(components, list) or len(components) != 3:
        raise SystemExit("components.lock.json must contain exactly three components")
    for item in components:
        if not isinstance(item, dict) or any(field not in item for field in lock_required):
            raise SystemExit("components.lock.json component is missing a required field")


def read_lock_mapping(lock):
    mapping = {}
    for item in lock["components"]:
        path = item["path"]
        if path in mapping or path not in expected_paths:
            raise SystemExit(f"unexpected or duplicate component path in lock: {path!r}")
        commit = item["commit"]
        if not isinstance(commit, str) or full_commit.fullmatch(commit) is None:
            raise SystemExit(f"component commit is not a lowercase 40-hex object ID: {path}")
        mapping[path] = commit
    if set(mapping) != expected_paths:
        raise SystemExit(f"component path set mismatch: {set(mapping)!r}")
    return mapping


def validate_component_policy(lock):
    for item in lock["components"]:
        policy = expected_policy[item["path"]]
        for field in ("name", "repository", "branch"):
            if item[field] != policy[field]:
                raise SystemExit(
                    f"component policy mismatch for {item['path']} {field}: "
                    f"{item[field]!r} != {policy[field]!r}"
                )


def validate_submodule_policy():
    for path, policy in expected_policy.items():
        url = subprocess.check_output(
            ["git", "config", "-f", ".gitmodules", f"submodule.{path}.url"],
            cwd=root,
            text=True,
        ).strip()
        branch = subprocess.check_output(
            ["git", "config", "-f", ".gitmodules", f"submodule.{path}.branch"],
            cwd=root,
            text=True,
        ).strip()
        if url != policy["repository"]:
            raise SystemExit(f".gitmodules URL mismatch for {path}: {url!r}")
        if branch != policy["branch"]:
            raise SystemExit(f".gitmodules branch mismatch for {path}: {branch!r}")


def validate_parent_gitlinks(lock_mapping):
    try:
        current_mapping = resolve_current_components(root, lock_mapping)
    except CurrentComponentError as exc:
        raise SystemExit(str(exc)) from exc
    actual = {}
    for path in sorted(expected_paths):
        stage = subprocess.check_output(
            ["git", "ls-files", "--stage", "--", path], cwd=root, text=True
        ).split()
        if len(stage) < 2 or stage[0] != "160000":
            raise SystemExit(f"parent gitlink mode is not 160000 for {path}")
        actual[path] = stage[1]
        if actual[path] != current_mapping[path]:
            raise SystemExit(
                f"parent gitlink mismatch for {path}: {actual[path]} != {current_mapping[path]}"
            )
        head = subprocess.check_output(
            ["git", "-C", str(root / path), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != current_mapping[path]:
            raise SystemExit(
                f"checked-out component mismatch for {path}: {head} != {current_mapping[path]}"
            )


def validate_contract_identity(lock_mapping):
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"M01 build contract cannot be parsed: {exc}")
    components = contract.get("components")
    if contract.get("schema_version") != 1 or not isinstance(components, list) or len(components) != 3:
        raise SystemExit("M01 build contract schema or component count is invalid")
    contract_mapping = {}
    for item in components:
        if not isinstance(item, dict) or any(field not in item for field in contract_required):
            raise SystemExit("M01 build contract component is missing a required field")
        path = item["path"]
        if path in contract_mapping or path not in expected_paths:
            raise SystemExit(f"unexpected or duplicate contract component path: {path!r}")
        commit = item["commit"]
        if not isinstance(commit, str) or full_commit.fullmatch(commit) is None:
            raise SystemExit(f"contract commit is not a lowercase 40-hex object ID: {path}")
        contract_mapping[path] = commit
        if item.get("upx_enabled") is not False:
            raise SystemExit(f"UPX is not disabled for {path}")
    if set(contract_mapping) != expected_paths:
        raise SystemExit(f"contract component path set mismatch: {set(contract_mapping)!r}")
    if contract_mapping != lock_mapping:
        raise SystemExit(
            f"M01 build-contract component commits do not match components.lock.json: "
            f"{contract_mapping!r} != {lock_mapping!r}"
        )
    fdkernel = next(item for item in components if item["path"] == "components/fdkernel")
    if fdkernel.get("branch_metadata") != "nec98-current":
        raise SystemExit("fdkernel build contract tracking branch is not nec98-current")


lock = json.loads((root / "manifests/components.lock.json").read_text(encoding="utf-8"))
validate_lock_schema(lock)
lock_mapping = read_lock_mapping(lock)
validate_component_policy(lock)
validate_submodule_policy()
validate_parent_gitlinks(lock_mapping)
validate_contract_identity(lock_mapping)
print("parent gitlinks, component lock mapping, and M01 contract identities are exact")
PY
}

validate_contract_inputs() {
    python3 - "$M01_CONTRACT" "$M01_TOOLCHAIN_LOCK" "$M01_BASE_AMD64_DIGEST" <<'PY'
import json
import re
import sys
from pathlib import Path

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
lock = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if contract.get("schema_version") != 1 or contract.get("canonical_platform") != "linux/amd64":
    raise SystemExit("invalid M01 contract identity")
if len(contract.get("components", [])) != 3:
    raise SystemExit("M01 contract does not contain three components")
canonical = lock.get("canonical", {})
if canonical.get("architecture") != "linux/amd64":
    raise SystemExit("invalid canonical toolchain architecture")
if canonical.get("base_image", {}).get("amd64_manifest_digest") != sys.argv[3]:
    raise SystemExit("invalid locked base image digest")
if lock.get("container_build_inputs", {}).get("required_upx") is not False:
    raise SystemExit("UPX must be disabled")
open_watcom = canonical.get("open_watcom", {})
for field in ("release", "release_tag", "release_id", "tag_commit", "package", "asset_id", "asset_size", "publisher_md5", "sha256", "official_upstream_url", "official_github_url", "verification_method", "archive_format", "install_path", "required_host_directory", "host_tools"):
    if field not in open_watcom:
        raise SystemExit(f"Open Watcom lock is missing {field}")
if open_watcom["release"] != "Open Watcom 1.9" or open_watcom["release_tag"] != "ow1.9":
    raise SystemExit("Open Watcom lock does not select the final 1.9 release")
if not re.fullmatch(r"[0-9a-f]{40}", open_watcom["tag_commit"]):
    raise SystemExit("Open Watcom tag commit is not a lowercase 40-hex ID")
if not re.fullmatch(r"[0-9a-f]{64}", open_watcom["sha256"]):
    raise SystemExit("Open Watcom archive SHA-256 is not a lowercase 64-hex value")
if open_watcom["package"] != "open-watcom-c-linux-1.9" or open_watcom["archive_format"] != "zip":
    raise SystemExit("Open Watcom package identity is not the locked 1.9 ZIP")
if open_watcom["required_host_directory"] != "binl" or open_watcom["install_path"] != "/opt/openwatcom-1.9":
    raise SystemExit("Open Watcom install or host directory is not the locked 1.9 path")
if open_watcom["asset_size"] != 83959748 or open_watcom["asset_id"] != 44807673:
    raise SystemExit("Open Watcom package size or asset ID is not locked")
if open_watcom["publisher_md5"] != "960fe6b5cf88769a42949f5fedf62827":
    raise SystemExit("Open Watcom publisher MD5 is not locked")
if open_watcom["sha256"] != "f7484be27eb70028010303fc16bb2acc5a785679567a568b940c28190ddbf3f3":
    raise SystemExit("Open Watcom package SHA-256 is not locked")
print("M01 contract and toolchain lock are valid")
PY
}

record_host_runtime() {
    mkdir -p "$M01_RUNTIME_ROOT"
    local context_name server_version daemon_os daemon_arch host_os host_arch colima_version colima_status
    local local_available_kib docker_available_kib probe container_arch container_dpkg
    context_name=$(docker context show)
    server_version=$(docker version --format '{{.Server.Version}}')
    daemon_os=$(docker info --format '{{.OperatingSystem}}')
    daemon_arch=$(docker info --format '{{.Architecture}}')
    host_arch=$(uname -m)
    if command -v sw_vers >/dev/null 2>&1; then
        host_os=$(sw_vers -productVersion 2>/dev/null || printf '%s' unknown)
    else
        host_os=not-macos
    fi
    if command -v colima >/dev/null 2>&1; then
        colima_version=$(colima version 2>/dev/null | head -n 1 || printf '%s' unavailable)
        if colima status >/dev/null 2>&1; then colima_status=running; else colima_status=not-running; fi
    else
        colima_version=not-installed
        colima_status=not-present
    fi
    local_available_kib=$(df -Pk "$M01_ROOT" | awk 'NR==2 {print $4}')
    [ "$local_available_kib" -ge 8388608 ] || fail "repository filesystem has less than 8 GiB available"
    probe=$(docker run --rm --platform "$M01_PLATFORM" --network=none \
        "$M01_BASE_IMAGE@$M01_BASE_AMD64_DIGEST" \
        sh -c 'uname -m; dpkg --print-architecture; df -Pk /')
    container_arch=$(printf '%s\n' "$probe" | sed -n '1p')
    container_dpkg=$(printf '%s\n' "$probe" | sed -n '2p')
    docker_available_kib=$(printf '%s\n' "$probe" | awk 'NR==4 {print $4}')
    [ "$container_arch" = x86_64 ] || fail "canonical container did not report x86_64"
    [ "$container_dpkg" = amd64 ] || fail "canonical container did not report amd64"
    [ "${docker_available_kib:-0}" -ge 8388608 ] || fail "Docker filesystem has less than 8 GiB available"
    python3 - "$M01_RUNTIME_ROOT/host.json" "$context_name" "$server_version" "$daemon_os" "$daemon_arch" "$host_os" "$host_arch" "$colima_version" "$colima_status" "$container_arch" "$container_dpkg" "$local_available_kib" "$docker_available_kib" <<'PY'
import json
import sys
from pathlib import Path

keys = [
    "context", "docker_server_version", "daemon_os", "daemon_architecture",
    "host_os_version", "host_architecture", "colima_version", "colima_status",
    "container_architecture", "container_dpkg_architecture", "repository_available_kib",
    "docker_visible_available_kib",
]
data = dict(zip(keys, sys.argv[2:]))
data["canonical_platform"] = "linux/amd64"
data["adapter_path"] = "unknown"
data["adapter_path_note"] = "Actual amd64 execution succeeded; Colima status did not explicitly declare Rosetta or QEMU."
data["golden_inputs"] = "Host adapter fields are diagnostic only."
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
    printf 'M01 host preflight passed: context=%s daemon=%s container=%s/%s\n' "$context_name" "$daemon_arch" "$container_arch" "$container_dpkg"
}

record_host_portability_audit() {
    python3 - "$M01_RUNTIME_ROOT/host-portability-audit.json" "$M01_ROOT" <<'PY'
import json
import sys
from pathlib import Path

output_path = Path(sys.argv[1])
root = Path(sys.argv[2])
patterns = (
    "stat -c",
    "readlink -f",
    "realpath",
    "sed -r",
    "grep -P",
    "find -printf",
    "date -d",
    "xargs -r",
    "sort -V",
    "sha256sum",
    "md5sum",
    "mktemp",
)
host_paths = {
    "Makefile",
    "tools/verify_scaffold.py",
    "tools/m01/build_baseline.sh",
    "tools/m01/host_fs.py",
    "tools/m01/test_host_portability.sh",
}
container_paths = {
    "containers/m01/Dockerfile",
    "containers/m01/build-entrypoint.sh",
    "tools/m01/container/image_tool_probe.sh",
}
data_paths = {"manifests/toolchains.lock.json"}
records = []
for relative in sorted(host_paths | container_paths | data_paths):
    path = root / relative
    if not path.is_file():
        continue
    if relative in host_paths:
        execution_class = "host-executed"
    elif relative in container_paths:
        execution_class = "container-executed"
    else:
        execution_class = "data-text"
    lines = path.read_text(encoding="utf-8").splitlines()
    audit_start = None
    audit_end = None
    if relative == "tools/m01/build_baseline.sh":
        audit_start = next((index for index, value in enumerate(lines, 1) if value == "record_host_portability_audit() {"), None)
        audit_end = next((index for index, value in enumerate(lines, 1) if value == "download_verified_openwatcom() {"), None)
    for line_number, line in enumerate(lines, 1):
        for pattern in patterns:
            if pattern in line:
                line_class = execution_class
                if relative == "tools/m01/build_baseline.sh" and audit_start and audit_end and audit_start <= line_number < audit_end:
                    line_class = "data-text"
                if relative == "tools/m01/test_host_portability.sh" and line_number >= 75:
                    line_class = "data-text"
                records.append({
                    "file": relative,
                    "line": line_number,
                    "pattern": pattern,
                    "execution_class": line_class,
                })
corrections = [
    {
        "file": "tools/m01/build_baseline.sh",
        "pattern": "stat -c",
        "action": "replaced host mode and size inspection with tools/m01/host_fs.py",
    },
    {
        "file": "tools/m01/build_baseline.sh",
        "pattern": "sha256sum/md5sum/shasum",
        "action": "replaced host digest commands with tools/m01/host_fs.py",
    },
]
data = {
    "schema_version": 1,
    "scope": "M01 parent commands and referenced container command text",
    "records": records,
    "corrections": corrections,
    "policy": "Only host-executed commands are subject to macOS portability correction; container syntax is evaluated in Linux containers.",
}
with output_path.open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
}

preflight() {
    command -v git >/dev/null 2>&1 || fail "git is unavailable"
    command -v docker >/dev/null 2>&1 || fail "docker is unavailable"
    docker info >/dev/null || fail "docker info failed"
    validate_gitlinks
    validate_contract_inputs
    python3 tools/verify_scaffold.py
    local metadata amd64_name
    metadata=$(docker buildx imagetools inspect "$M01_BASE_IMAGE@$M01_BASE_INDEX_DIGEST")
    printf '%s\n' "$metadata" | grep -F "Digest:    $M01_BASE_INDEX_DIGEST" >/dev/null || fail "Ubuntu index digest does not match the lock"
    amd64_name=$(printf '%s\n' "$metadata" | awk '/^  Name:/ {name=$0} /^  Platform:[[:space:]]+linux\/amd64$/ {print name}')
    printf '%s\n' "$amd64_name" | grep -F "$M01_BASE_AMD64_DIGEST" >/dev/null || fail "Ubuntu amd64 manifest digest does not match the lock"
    record_host_runtime
    record_host_portability_audit
}

download_verified_openwatcom() {
    local stage_root=$M01_RESULTS_ROOT/toolchain
    local first_copy=$stage_root/.first-$M01_OW_PACKAGE
    local second_copy=$stage_root/$M01_OW_PACKAGE
    local first_size first_md5 first_sha second_size second_md5 second_sha
    [ ! -e "$stage_root" ] || fail "Open Watcom staging directory already exists; run m01-clean before image construction"
    mkdir -p "$stage_root"
    curl --fail --location --retry 3 --output "$first_copy" "$M01_OW_OFFICIAL_UPSTREAM_URL"
    first_size=$(wc -c <"$first_copy" | tr -d '[:space:]')
    first_md5=$(portable_file_hash md5 "$first_copy")
    first_sha=$(portable_file_hash sha256 "$first_copy")
    [ "$first_size" = "$M01_OW_PACKAGE_SIZE" ] || fail "first Open Watcom download size mismatch"
    [ "$first_md5" = "$M01_OW_PUBLISHER_MD5" ] || fail "first Open Watcom download MD5 mismatch"
    [ "$first_sha" = "$M01_OW_PACKAGE_SHA256" ] || fail "first Open Watcom download SHA-256 mismatch"
    curl --fail --location --retry 3 --output "$second_copy" "$M01_OW_OFFICIAL_GITHUB_URL"
    second_size=$(wc -c <"$second_copy" | tr -d '[:space:]')
    second_md5=$(portable_file_hash md5 "$second_copy")
    second_sha=$(portable_file_hash sha256 "$second_copy")
    [ "$second_size" = "$M01_OW_PACKAGE_SIZE" ] || fail "second Open Watcom download size mismatch"
    [ "$second_md5" = "$M01_OW_PUBLISHER_MD5" ] || fail "second Open Watcom download MD5 mismatch"
    [ "$second_sha" = "$M01_OW_PACKAGE_SHA256" ] || fail "second Open Watcom download SHA-256 mismatch"
    cmp -s "$first_copy" "$second_copy" || fail "independent Open Watcom downloads are not byte-identical"
    python3 - "$first_copy" <<'PY'
import sys
from pathlib import Path

Path(sys.argv[1]).unlink()
PY
    [ ! -e "$first_copy" ] || fail "first Open Watcom download was not deleted"
    chmod 0444 "$second_copy"
    python3 - "$M01_RUNTIME_ROOT/toolchain-download.json" "$M01_OW_RELEASE" "$M01_OW_RELEASE_TAG" "$M01_OW_RELEASE_ID" "$M01_OW_TAG_COMMIT" "$M01_OW_PACKAGE" "$M01_OW_ASSET_ID" "$M01_OW_PACKAGE_SIZE" "$M01_OW_PUBLISHER_MD5" "$M01_OW_PACKAGE_SHA256" "$M01_OW_OFFICIAL_UPSTREAM_URL" "$M01_OW_OFFICIAL_GITHUB_URL" "$M01_OW_VERIFICATION_METHOD" "$first_size" "$first_md5" "$first_sha" "$second_size" "$second_md5" "$second_sha" <<'PY'
import json
import sys
from pathlib import Path

data = {
    "release": sys.argv[2],
    "release_tag": sys.argv[3],
    "release_id": int(sys.argv[4]),
    "tag_commit": sys.argv[5],
    "package": sys.argv[6],
    "asset_id": int(sys.argv[7]),
    "package_size": int(sys.argv[8]),
    "publisher_md5": sys.argv[9],
    "package_sha256": sys.argv[10],
    "official_upstream_url": sys.argv[11],
    "official_github_url": sys.argv[12],
    "verification_method": sys.argv[13],
    "first_download": {"source": "official_upstream", "size": int(sys.argv[14]), "md5": sys.argv[15], "sha256": sys.argv[16], "deleted": True},
    "second_download": {"source": "official_github_release", "size": int(sys.argv[17]), "md5": sys.argv[18], "sha256": sys.argv[19], "verified": True},
    "byte_identical": True,
    "archive_path": "qa/results/m01/toolchain/open-watcom-c-linux-1.9",
}
output_path = Path(sys.argv[1])
output_path.parent.mkdir(parents=True, exist_ok=True)
with output_path.open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
}

stage_image_probe_inputs() {
    local staging_root staged_script staged_data temporary_data
    staging_root=$M01_RUNTIME_ROOT/image-probe-input
    staged_script=$staging_root/image_tool_probe.sh
    staged_data=$staging_root/image-tool-probe.env
    temporary_data=$staged_data.tmp-$$
    [ ! -e "$staging_root" ] || fail "image probe staging directory already exists; run m01-clean before image construction"
    mkdir -p "$staging_root"
    install -m 0444 "$M01_ROOT/tools/m01/container/image_tool_probe.sh" "$staged_script"
    python3 - "$M01_TOOLCHAIN_LOCK" "$temporary_data" <<'PY'
import json
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
tools = lock["canonical"]["open_watcom"]["host_tools"]
expected = ["wcc", "wcl", "wmake", "wlink", "wasm", "wlib"]
if [tool.get("name") for tool in tools] != expected:
    raise SystemExit("Open Watcom host tool list is not canonical")
with Path(sys.argv[2]).open("w", encoding="utf-8", newline="\n") as stream:
    for tool in tools:
        prefix = "M01_PROBE_" + tool["name"].upper()
        stream.write(f"{prefix}_SIZE={tool['size']}\n")
        stream.write(f"{prefix}_SHA256={tool['sha256']}\n")
        stream.write(f"{prefix}_BANNER={tool['banner']}\n")
PY
    install -m 0444 "$temporary_data" "$staged_data"
    rm -f "$temporary_data"
    [ -f "$staged_script" ] && [ ! -L "$staged_script" ] || fail "staged image probe script is not a regular file"
    [ -f "$staged_data" ] && [ ! -L "$staged_data" ] || fail "staged image probe data is not a regular file"
    require_mode_0444 "$staged_script"
    require_mode_0444 "$staged_data"
    M01_PROBE_SCRIPT_SHA256=$(portable_file_hash sha256 "$staged_script")
    M01_PROBE_DATA_SHA256=$(portable_file_hash sha256 "$staged_data")
    M01_PROBE_SCRIPT_RELATIVE=qa/results/m01/runtime/image-probe-input/image_tool_probe.sh
    M01_PROBE_DATA_RELATIVE=qa/results/m01/runtime/image-probe-input/image-tool-probe.env
    M01_PROBE_SCRIPT_SIZE=$(portable_file_size "$staged_script")
    M01_PROBE_DATA_SIZE=$(portable_file_size "$staged_data")
}

validate_sha256_identity() {
    [ "$#" -eq 2 ] || fail "validate_sha256_identity expects a label and value"
    local label=$1 value=$2
    [[ "$value" =~ ^sha256:[0-9a-f]{64}$ ]] || fail "$label is not a full lowercase SHA-256 identity: $value"
}

cleanup_image_probe_container() {
    local cleanup_id=${probe_container_id:-}
    local retain=${retain_probe_container:-0}
    local probe_state
    [ -n "$cleanup_id" ] || return 0
    if ! [[ "$cleanup_id" =~ ^[0-9a-f]{64}$ ]]; then
        printf 'refusing invalid image probe container ID: %s\n' "$cleanup_id" >&2
        return 0
    fi
    if [ "$retain" -eq 1 ]; then
        printf 'retaining image probe container for exact-ID diagnostics: %s\n' "$cleanup_id" >&2
        return 0
    fi
    if docker inspect "$cleanup_id" >/dev/null 2>&1; then
        probe_state=$(docker inspect "$cleanup_id" --format '{{.State.Status}}')
        case "$probe_state" in
            created|exited|dead)
                printf 'removing exact image probe container: %s (%s)\n' "$cleanup_id" "$probe_state" >&2
                docker rm "$cleanup_id" >/dev/null
                ;;
            running)
                printf 'error: image probe container remains running: %s\n' "$cleanup_id" >&2
                ;;
            *) printf 'error: refusing unexpected image probe container state: %s\n' "$probe_state" >&2 ;;
        esac
    fi
}

record_image_probe_container() {
    local record_path=$1 inspect_json=$2 image_reference=$3 resolved_local_image_config_id=$4 start_status=$5 wait_status=$6 process_status=$7 phase=$8
    python3 - "$record_path" "$inspect_json" "$image_reference" "$resolved_local_image_config_id" "$start_status" "$wait_status" "$process_status" "$phase" "$M01_PROBE_SCRIPT_RELATIVE" "$M01_PROBE_SCRIPT_SIZE" "$M01_PROBE_SCRIPT_SHA256" "$M01_PROBE_DATA_RELATIVE" "$M01_PROBE_DATA_SIZE" "$M01_PROBE_DATA_SHA256" <<'PY'
import json
import re
import sys
from pathlib import Path

inspect = json.loads(sys.argv[2])[0]
mounts = inspect.get("Mounts", [])
network = inspect.get("HostConfig", {}).get("NetworkMode")
entrypoint = inspect.get("Config", {}).get("Entrypoint")
command = inspect.get("Config", {}).get("Cmd")
container_runtime_image_config_id = inspect.get("Image")
container_config_image_reference = inspect.get("Config", {}).get("Image")
resolved_local_image_config_id = sys.argv[4]
errors = []
if mounts != []:
    errors.append("image probe container has unexpected mounts")
if network != "none":
    errors.append("image probe container does not use network mode none")
digest_pattern = re.compile(r"^sha256:[0-9a-f]{64}$")
for label, value in (("resolved local image config ID", resolved_local_image_config_id), ("container runtime image config ID", container_runtime_image_config_id)):
    if not isinstance(value, str) or digest_pattern.fullmatch(value) is None:
        errors.append(f"{label} is not a full lowercase SHA-256 identity: {value!r}")
if container_runtime_image_config_id != resolved_local_image_config_id:
    errors.append("image probe container runtime image config ID does not match the resolved local image config ID")
if container_config_image_reference != sys.argv[3]:
    errors.append("image probe container Config.Image does not match the create reference")
if entrypoint != ["/bin/sh"] or command != ["/input/image_tool_probe.sh"]:
    errors.append("image probe container command is not the expected argv")

def optional_int(value):
    return None if value == "none" else int(value)

record = {
    "container_id": inspect.get("Id"),
    "container_state": inspect.get("State", {}).get("Status"),
    "image_reference": sys.argv[3],
    "resolved_local_image_config_id": resolved_local_image_config_id,
    "container_config_image_reference": container_config_image_reference,
    "container_runtime_image_config_id": container_runtime_image_config_id,
    "image_config_id_match": container_runtime_image_config_id == resolved_local_image_config_id,
    "requested_platform": "linux/amd64",
    "network_mode": network,
    "mounts": mounts,
    "command_argv": ["/bin/sh", "/input/image_tool_probe.sh"],
    "config_entrypoint": entrypoint,
    "config_cmd": command,
    "staged_script": {
        "path": sys.argv[9],
        "mode": "0444",
        "size": int(sys.argv[10]),
        "sha256": sys.argv[11],
    },
    "staged_data": {
        "path": sys.argv[12],
        "mode": "0444",
        "size": int(sys.argv[13]),
        "sha256": sys.argv[14],
    },
    "phase": sys.argv[8],
    "start_status": optional_int(sys.argv[5]),
    "wait_status": optional_int(sys.argv[6]),
    "process_status": optional_int(sys.argv[7]),
    "diagnostics_path": "qa/results/m01/runtime/image-tool-selection.txt",
}
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
if errors:
    raise SystemExit("; ".join(errors))
PY
}

record_image() {
    assert_prestart_lifecycle_policy
    mkdir -p "$M01_RUNTIME_ROOT"
    local image_reference resolved_local_image_config_id image_arch image_os repo_digests dockerfile_sha
    local tool_selection_file tool_selection_sha wmake_version
    local staged_script staged_data probe_container inspect_json
    local start_status wait_status wait_output process_status log_status probe_state
    image_reference=$M01_IMAGE_TAG
    resolved_local_image_config_id=$(docker image inspect "$image_reference" --format '{{.Id}}')
    validate_sha256_identity resolved_local_image_config_id "$resolved_local_image_config_id"
    image_arch=$(docker image inspect "$resolved_local_image_config_id" --format '{{.Architecture}}')
    image_os=$(docker image inspect "$resolved_local_image_config_id" --format '{{.Os}}')
    repo_digests=$(docker image inspect "$resolved_local_image_config_id" --format '{{json .RepoDigests}}')
    dockerfile_sha=$(portable_file_hash sha256 containers/m01/Dockerfile)
    [ "$image_arch" = amd64 ] || fail "built image architecture is not amd64"
    [ "$image_os" = linux ] || fail "built image OS is not Linux"
    stage_image_probe_inputs
    staged_script=$M01_RUNTIME_ROOT/image-probe-input/image_tool_probe.sh
    staged_data=$M01_RUNTIME_ROOT/image-probe-input/image-tool-probe.env
    tool_selection_file=$M01_RUNTIME_ROOT/image-tool-selection.txt
    probe_container=freedos-m01-image-probe-$$
    probe_container_id=
    retain_probe_container=1
    trap cleanup_image_probe_container EXIT
    docker create --platform "$M01_PLATFORM" --network=none \
        --name "$probe_container" \
        --entrypoint /bin/sh \
        --env M01_PROBE_SCRIPT_SHA256="$M01_PROBE_SCRIPT_SHA256" \
        --env M01_PROBE_DATA_SHA256="$M01_PROBE_DATA_SHA256" \
        --env M01_PROBE_DATA_PATH=/input/image-tool-probe.env \
        "$resolved_local_image_config_id" /input/image_tool_probe.sh >/dev/null
    probe_container_id=$(docker inspect "$probe_container" --format '{{.Id}}')
    [[ "$probe_container_id" =~ ^[0-9a-f]{64}$ ]] || fail "created image probe container ID is not a full lowercase 64-character ID"
    inspect_json=$(docker inspect "$probe_container_id")
    record_image_probe_container "$M01_RUNTIME_ROOT/image-probe-container.json" "$inspect_json" "$resolved_local_image_config_id" "$resolved_local_image_config_id" none none none created
    docker cp "$staged_script" "$probe_container_id:/input/image_tool_probe.sh"
    docker cp "$staged_data" "$probe_container_id:/input/image-tool-probe.env"
    start_status=0
    docker start "$probe_container_id" >"$M01_RUNTIME_ROOT/image-probe-start.txt" 2>&1 || start_status=$?
    wait_status=0
    wait_output=
    if [ "$start_status" -eq 0 ]; then
        wait_output=$(docker wait "$probe_container_id") || wait_status=$?
    fi
    log_status=0
    docker logs "$probe_container_id" >"$tool_selection_file.raw" 2>&1 || log_status=$?
    tail -n 4000 "$tool_selection_file.raw" >"$tool_selection_file.bounded"
    mv "$tool_selection_file.bounded" "$tool_selection_file"
    process_status=
    if [ "$wait_status" -eq 0 ] && printf '%s\n' "$wait_output" | grep -E '^[0-9]+$' >/dev/null; then
        process_status=$(printf '%s\n' "$wait_output" | tail -n 1)
    else
        process_status=$(docker inspect "$probe_container_id" --format '{{.State.ExitCode}}')
    fi
    inspect_json=$(docker inspect "$probe_container_id")
    record_image_probe_container "$M01_RUNTIME_ROOT/image-probe-container.json" "$inspect_json" "$resolved_local_image_config_id" "$resolved_local_image_config_id" "$start_status" "$wait_status" "$process_status" completed
    probe_state=$(docker inspect "$probe_container_id" --format '{{.State.Status}}')
    if [ "$start_status" -ne 0 ] || [ "$wait_status" -ne 0 ] || [ "$log_status" -ne 0 ] || [ "$process_status" -ne 0 ]; then
        printf 'error: image tool probe failed: state=%s start=%s wait=%s process=%s logs=%s\n' "$probe_state" "$start_status" "$wait_status" "$process_status" "$log_status" >&2
        fail "image tool probe did not pass"
    fi
    grep -F 'wcc_probe_status=0' "$tool_selection_file" >/dev/null || fail "image tool probe lacks successful WCC status"
    grep -F 'wmake_probe_status=0' "$tool_selection_file" >/dev/null || fail "image tool probe lacks successful WMake status"
    grep -Fx 'M01_WMAKE_PROBE_OK' "$tool_selection_file" >/dev/null || fail "image tool probe lacks WMake token"
    grep -F 'wmake_probe_output_match=true' "$tool_selection_file" >/dev/null || fail "image tool probe lacks probe.ok byte match"
    if grep -E 'F38|E02|Error\(' "$tool_selection_file" >/dev/null; then
        fail "image tool probe contains a WMake error diagnostic"
    fi
    tool_selection_sha=$(portable_file_hash sha256 "$tool_selection_file")
    wmake_version=$(awk '/Open Watcom Make Version/ {print; exit}' "$tool_selection_file")
    [ -n "$wmake_version" ] || fail "image tool-selection proof did not record Open Watcom version"
    docker rm "$probe_container_id" >/dev/null
    probe_container_id=
    retain_probe_container=0
    trap - EXIT
    python3 - "$M01_IMAGE_FILE" "$image_reference" "$resolved_local_image_config_id" "$image_arch" "$image_os" "$repo_digests" "$dockerfile_sha" "$M01_BASE_AMD64_DIGEST" "$M01_OW_RELEASE" "$M01_OW_RELEASE_TAG" "$M01_OW_RELEASE_ID" "$M01_OW_TAG_COMMIT" "$M01_OW_PACKAGE" "$M01_OW_ASSET_ID" "$M01_OW_PACKAGE_SIZE" "$M01_OW_PUBLISHER_MD5" "$M01_OW_PACKAGE_SHA256" "$M01_OW_OFFICIAL_UPSTREAM_URL" "$M01_OW_OFFICIAL_GITHUB_URL" "$M01_OW_VERIFICATION_METHOD" "$tool_selection_sha" "$wmake_version" <<'PY'
import json
import sys
from pathlib import Path

data = {
    "image_reference": sys.argv[2],
    "resolved_local_image_config_id": sys.argv[3],
    "architecture": sys.argv[4],
    "os": sys.argv[5],
    "repo_digests": json.loads(sys.argv[6]),
    "dockerfile_sha256": sys.argv[7],
    "base_amd64_manifest_digest": sys.argv[8],
    "requested_platform": "linux/amd64",
    "resolved_image_id_policy": "Runtime-only identifier; not a deterministic golden input.",
    "open_watcom": {
        "release": sys.argv[9],
        "release_tag": sys.argv[10],
        "release_id": int(sys.argv[11]),
        "tag_commit": sys.argv[12],
        "package": sys.argv[13],
        "asset_id": int(sys.argv[14]),
        "package_size": int(sys.argv[15]),
        "publisher_md5": sys.argv[16],
        "package_sha256": sys.argv[17],
        "official_upstream_url": sys.argv[18],
        "official_github_url": sys.argv[19],
        "verification_method": sys.argv[20],
        "verified_second_copy": True,
        "tool_selection_evidence": "qa/results/m01/runtime/image-tool-selection.txt",
        "tool_selection_sha256": sys.argv[21],
        "wmake_version_output": sys.argv[22],
    },
}
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
    printf 'M01 image recorded: %s (%s)\n' "$resolved_local_image_config_id" "$image_arch"
}
image() {
    assert_prestart_lifecycle_policy
    command -v docker >/dev/null 2>&1 || fail "docker is unavailable"
    download_verified_openwatcom
    docker build --platform "$M01_PLATFORM" \
        --no-cache \
        --build-arg "APT_SNAPSHOT=$M01_APT_SNAPSHOT" \
        --build-arg "OW_PACKAGE_SIZE=$M01_OW_PACKAGE_SIZE" \
        --build-arg "OW_PUBLISHER_MD5=$M01_OW_PUBLISHER_MD5" \
        --build-arg "OW_PACKAGE_SHA256=$M01_OW_PACKAGE_SHA256" \
        --build-context "m01-toolchain=$M01_RESULTS_ROOT/toolchain" \
        --tag "$M01_IMAGE_TAG" \
        --file containers/m01/Dockerfile containers/m01
    record_image
    record_host_runtime
    record_host_portability_audit
}

archive_component() {
    local component=$1 archive_name=$2 commit=$3
    local archive_path=$M01_SOURCE_ROOT/$archive_name
    if git -C "components/$component" status --short --untracked-files=all | grep . >/dev/null; then
        fail "component is dirty: $component"
    fi
    local temporary_archive=${archive_path}.tmp-$$
    git -C "components/$component" archive --format=tar --prefix="$component/" "$commit" >"$temporary_archive"
    chmod 0444 "$temporary_archive"
    mv -f "$temporary_archive" "$archive_path"
    portable_file_hash sha256 "$archive_path"
}

locked_component_commit() {
    local path=$1
    python3 - "$M01_ROOT/manifests/components.lock.json" "$path" <<'PY'
import json
import sys
from pathlib import Path

lock = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for component in lock["components"]:
    if component["path"] == sys.argv[2]:
        print(component["commit"])
        break
else:
    raise SystemExit(f"component is absent from the lock: {sys.argv[2]}")
PY
}

append_container_record() {
    local run_id=$1 component=$2 inspect_json=$3 exit_code=$4 start_status=$5
    python3 - "$M01_RESULTS_ROOT/$run_id/.container-$component.json" "$component" "$inspect_json" "$exit_code" "$start_status" "$M01_RESOLVED_LOCAL_IMAGE_CONFIG_ID" "$M01_IMAGE_TAG" <<'PY'
import json
import re
import sys
from pathlib import Path

inspect = json.loads(sys.argv[3])[0]
mounts = inspect.get("Mounts", [])
network = inspect.get("HostConfig", {}).get("NetworkMode")
if mounts != []:
    raise SystemExit("container had an unexpected mount")
if network != "none":
    raise SystemExit("container did not use network mode none")
if inspect.get("Config", {}).get("Image") != sys.argv[7]:
    raise SystemExit("container image reference changed")
runtime_image_config_id = inspect.get("Image")
if not isinstance(runtime_image_config_id, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", runtime_image_config_id) is None:
    raise SystemExit("container runtime image config ID is not a full lowercase SHA-256 identity")
if runtime_image_config_id != sys.argv[6]:
    raise SystemExit("component container runtime image config ID does not match the resolved local image config ID")
record = {
    "component": sys.argv[2],
    "container_id": inspect.get("Id"),
    "resolved_local_image_config_id": sys.argv[6],
    "container_runtime_image_config_id": runtime_image_config_id,
    "container_config_image_reference": inspect.get("Config", {}).get("Image"),
    "requested_platform": "linux/amd64",
    "mounts": mounts,
    "network_mode": network,
    "exit_code": int(sys.argv[4]),
    "start_status": int(sys.argv[5]),
}
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(record, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
}

finish_container_records() {
    local run_id=$1
    python3 - "$M01_RESULTS_ROOT/$run_id" "$M01_RUNTIME_ROOT/$run_id-container.json" <<'PY'
import json
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
records = []
for path in sorted(run_dir.glob(".container-*.json")):
    records.append(json.loads(path.read_text(encoding="utf-8")))
    path.unlink()
with Path(sys.argv[2]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(records, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
}

copy_output() {
    local container=$1 run_dir=$2 component=$3
    mkdir -p "$run_dir/artifacts" "$run_dir/logs" "$run_dir/container-manifests" "$run_dir/tool-versions" "$run_dir/tool-selections"
    docker cp "$container:/output/artifacts/." "$run_dir/artifacts/"
    docker cp "$container:/output/logs/." "$run_dir/logs/"
    docker cp "$container:/output/container-manifest.json" "$run_dir/container-manifests/$component.json"
    docker cp "$container:/output/tool-versions.txt" "$run_dir/tool-versions/$component.txt"
    docker cp "$container:/output/tool-selection.txt" "$run_dir/tool-selections/$component.txt"
    if [ "$component" = freecom ]; then
        docker cp "$container:/output/freecom-timestamp.json" "$run_dir/tool-versions/freecom-timestamp.json"
        docker cp "$container:/output/freecom-watcomc.cfg" "$run_dir/tool-versions/freecom-watcomc.cfg"
    fi
    if [ "$component" = fdkernel ]; then
        mkdir -p "$run_dir/diagnostics"
        if docker cp "$container:/output/diagnostics/." "$run_dir/diagnostics/" 2>/dev/null; then :; fi
    fi
}

assert_prestart_lifecycle_policy() {
    # Inputs must be transferred with docker cp while the container is stopped.
    # docker exec is forbidden in the M01 pre-start lifecycle.
    if grep -nE '^[[:space:]]*docker[[:space:]]+exec([[:space:]]|$)' "$M01_SCRIPT_DIR/build_baseline.sh" >/dev/null; then
        fail "M01 pre-start lifecycle must not use docker exec"
    fi
    [ -f "$M01_ROOT/tools/m01/container/image_tool_probe.sh" ] || fail "standalone image probe script is missing"
    python3 - "$M01_SCRIPT_DIR/build_baseline.sh" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = text.index("record_image() {")
end = text.index("\nimage() {", start)
block = text[start:end]
for forbidden in ("docker run", "docker exec", "sh -c", " -c '"):
    if forbidden in block:
        raise SystemExit(f"image probe lifecycle contains forbidden construct: {forbidden}")
for required in ("docker create", "docker cp", "docker start", "docker wait", "image_tool_probe.sh"):
    if required not in block:
        raise SystemExit(f"image probe lifecycle lacks required construct: {required}")
if '"$resolved_local_image_config_id" /input/image_tool_probe.sh' not in block:
    raise SystemExit("image probe command is not passed with the resolved config ID")
PY
}

stage_fdkernel_configuration() {
    local run_dir=$1
    local staged_configuration=$run_dir/input-staging/fdkernel-nec98.mak
    local temporary_configuration=${staged_configuration}.tmp-$$
    mkdir -p "$(dirname "$staged_configuration")"
    python3 - "$M01_ROOT/config/m01/fdkernel-nec98.mak" "$M01_FDKERNEL_BUILD_DATE" "$temporary_configuration" <<'PY'
import re
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
date = sys.argv[2]
output_path = Path(sys.argv[3])
if re.fullmatch(r"[A-Z][a-z]{2} [ 0-9][0-9] [0-9]{4}", date) is None or len(date) != 11:
    raise SystemExit("fdkernel build date is not a C-compatible 11-byte value")
source = source_path.read_text(encoding="utf-8")
if "KERNEL_BUILD_DATE" in source:
    raise SystemExit("fdkernel configuration already contains a deterministic date definition")
encoded_date = date.replace(" ", r"\ ")
line = f'ALLCFLAGS=-DKERNEL_BUILD_DATE=\\"{encoded_date}\\" \n'
with output_path.open("w", encoding="utf-8", newline="\n") as stream:
    stream.write(source + line)
PY
    install -m 0444 "$temporary_configuration" "$staged_configuration"
    rm -f -- "$temporary_configuration"
    python3 - "$staged_configuration" <<'PY'
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file() or path.is_symlink() or path.name != "fdkernel-nec98.mak":
    raise SystemExit("staged fdkernel configuration is not the expected regular file")
if (path.stat().st_mode & 0o777) != 0o444:
    raise SystemExit("staged fdkernel configuration mode is not exactly 0444")
PY
    printf '%s\n' "$staged_configuration"
}

stage_freecom_configuration() {
    local run_dir=$1
    local staged_configuration=$run_dir/input-staging/freecom-nec98.mak
    local temporary_configuration=${staged_configuration}.tmp-$$
    mkdir -p "$(dirname "$staged_configuration")"
    python3 - "$M01_ROOT/components/freecom/config.std" "$M01_FREECOM_TIMESTAMP" "$temporary_configuration" <<'PY'
import json
import re
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
timestamp_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])
source = source_path.read_text(encoding="utf-8")
timestamp = json.loads(timestamp_path.read_text(encoding="utf-8"))
date = timestamp.get("formatted_date")
time = timestamp.get("formatted_time")
if not isinstance(date, str) or not re.fullmatch(r"[A-Z][a-z]{2} [ 0-9][0-9] [0-9]{4}", date):
    raise SystemExit("FreeCOM build date is not a C-compatible value")
if not isinstance(time, str) or not re.fullmatch(r"[0-9]{2}:[0-9]{2}:[0-9]{2}", time):
    raise SystemExit("FreeCOM build time is not a C-compatible value")
marker = "$(CFG):"
if source.count(marker) != 1:
    raise SystemExit("FreeCOM config.std does not contain exactly one CFG target")
if "FREECOM_BUILD_DATE" in source or "FREECOM_BUILD_TIME" in source:
    raise SystemExit("FreeCOM config.std already contains deterministic timestamp definitions")
line = f'CFLAGS2 = -DFREECOM_BUILD_DATE=\\"{date}\\" -DFREECOM_BUILD_TIME=\\"{time}\\"\n'
source = source.replace(marker, line + marker, 1)
with output_path.open("w", encoding="utf-8", newline="\n") as stream:
    stream.write(source)
PY
    install -m 0444 "$temporary_configuration" "$staged_configuration"
    rm -f -- "$temporary_configuration"
    python3 - "$staged_configuration" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file() or path.is_symlink() or path.name != "freecom-nec98.mak":
    raise SystemExit("staged FreeCOM configuration is not the expected regular file")
if (path.stat().st_mode & 0o777) != 0o444:
    raise SystemExit("staged FreeCOM configuration mode is not exactly 0444")
PY
    printf '%s\n' "$staged_configuration"
}

remove_recorded_container() {
    local record=$1 container_id container_state
    [ -f "$record" ] || return 0
    container_id=$(python3 - "$record" <<'PY'
import json
import re
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
value = data.get("container_id")
if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
    raise SystemExit("recorded container ID is not an exact 64-character hexadecimal ID")
print(value)
PY
)
    if docker inspect "$container_id" >/dev/null 2>&1; then
        container_state=$(docker inspect "$container_id" --format '{{.State.Status}}')
        case "$container_state" in
            created|exited|dead) ;;
            *) fail "refusing to remove recorded container in unexpected state: $container_id ($container_state)" ;;
        esac
        printf 'removing retained exact container ID: %s (%s)\n' "$container_id" "$container_state"
        docker rm "$container_id" >/dev/null
    else
        printf 'retained exact container ID is already absent: %s\n' "$container_id"
    fi
}

run_one() {
    local run_id=$1
    local run_dir=$M01_RESULTS_ROOT/$run_id
    mkdir -p "$run_dir"
    local container container_id component archive_name archive_sha config_sha source_epoch inspect_json start_status wait_status exit_code
    local staged_configuration wait_output log_status
    local -a container_env_args
    local fdkernel_configuration_sha
    fdkernel_configuration_sha=$(portable_file_hash sha256 config/m01/fdkernel-nec98.mak)
    for component in fdkernel freecom country; do
        case "$component" in
            fdkernel) archive_name=fdkernel.tar ;;
            freecom) archive_name=freecom.tar ;;
            country) archive_name=country.tar ;;
        esac
        source_epoch=$(python3 - "$M01_CONTRACT" "components/$component" <<'PY'
import json
import sys
from pathlib import Path

contract = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
for component in contract["components"]:
    if component["path"] == sys.argv[2]:
        print(component["source_date_epoch"])
        break
else:
    raise SystemExit(f"component is absent from the build contract: {sys.argv[2]}")
PY
)
        config_sha=none
        staged_configuration=
        if [ "$component" = fdkernel ]; then
            staged_configuration=$(stage_fdkernel_configuration "$run_dir")
            config_sha=$(portable_file_hash sha256 "$staged_configuration")
        elif [ "$component" = freecom ]; then
            staged_configuration=$(stage_freecom_configuration "$run_dir")
            config_sha=$(portable_file_hash sha256 "$staged_configuration")
        fi
        archive_sha=$(portable_file_hash sha256 "$M01_SOURCE_ROOT/$archive_name")
        container=freedos-m01-${run_id}-${component}-$$
        container_env_args=(--env "SOURCE_DATE_EPOCH=$source_epoch" --env UMASK=022)
        if [ "${M01_DIAGNOSTICS-}" = 1 ]; then
            container_env_args+=(--env M01_DIAGNOSTICS=1)
        fi
        if [ "$component" = freecom ]; then
            container_env_args+=(--env "M01_FREECOM_BUILD_DATE=$M01_FREECOM_BUILD_DATE" --env "M01_FREECOM_BUILD_TIME=$M01_FREECOM_BUILD_TIME")
        fi
        docker create --platform "$M01_PLATFORM" --network=none \
            --name "$container" "${container_env_args[@]}" \
            "$M01_IMAGE_TAG" "$component" "$run_id" "$archive_name" "$archive_sha" "$config_sha" >/dev/null
        container_id=$(docker inspect "$container" --format '{{.Id}}')
        inspect_json=$(docker inspect "$container_id")
        append_container_record "$run_id" "$component" "$inspect_json" 125 125
        docker cp "$M01_SOURCE_ROOT/$archive_name" "$container_id:/input/$archive_name"
        if [ -n "$staged_configuration" ]; then
            case "$component" in
                fdkernel) docker cp "$staged_configuration" "$container_id:/input/fdkernel-nec98.mak" ;;
                freecom) docker cp "$staged_configuration" "$container_id:/input/freecom-nec98.mak" ;;
            esac
        fi
        start_status=0
        docker start "$container_id" >"$run_dir/.docker-start-$component.log" 2>&1 || start_status=$?
        wait_status=125
        wait_output=
        if [ "$start_status" -eq 0 ]; then
            wait_status=0
            wait_output=$(docker wait "$container_id") || wait_status=$?
        fi
        log_status=0
        docker logs "$container_id" >"$run_dir/.docker-$component.log" 2>&1 || log_status=$?
        tail -n 4000 "$run_dir/.docker-$component.log" >"$run_dir/.docker-$component.bounded"
        mv "$run_dir/.docker-$component.bounded" "$run_dir/docker-$component.log"
        if [ "$wait_status" -eq 0 ] && printf '%s\n' "$wait_output" | grep -E '^[0-9]+$' >/dev/null; then
            exit_code=$(printf '%s\n' "$wait_output" | tail -n 1)
        else
            exit_code=$(docker inspect "$container_id" --format '{{.State.ExitCode}}')
        fi
        inspect_json=$(docker inspect "$container_id")
        append_container_record "$run_id" "$component" "$inspect_json" "$exit_code" "$start_status"
        if [ "$start_status" -ne 0 ] || [ "$wait_status" -ne 0 ] || [ "$log_status" -ne 0 ] || [ "$exit_code" -ne 0 ]; then
            printf 'failed container %s; bounded diagnostics collected before removal\n' "$container" >&2
            mkdir -p "$run_dir/artifacts" "$run_dir/logs" "$run_dir/container-manifests" "$run_dir/tool-versions" "$run_dir/tool-selections"
            if docker cp "$container_id:/output/artifacts/." "$run_dir/artifacts/" 2>/dev/null; then :; fi
            if docker cp "$container_id:/output/logs/." "$run_dir/logs/" 2>/dev/null; then :; fi
            if docker cp "$container_id:/output/container-manifest.json" "$run_dir/container-manifests/$component.json" 2>/dev/null; then :; fi
            if docker cp "$container_id:/output/tool-versions.txt" "$run_dir/tool-versions/$component.txt" 2>/dev/null; then :; fi
            if docker cp "$container_id:/output/tool-selection.txt" "$run_dir/tool-selections/$component.txt" 2>/dev/null; then :; fi
            if [ "$component" = fdkernel ]; then
                mkdir -p "$run_dir/diagnostics"
                if docker cp "$container_id:/output/diagnostics/." "$run_dir/diagnostics/" 2>/dev/null; then :; fi
            fi
            if [ "$component" = freecom ]; then
                if docker cp "$container_id:/output/freecom-timestamp.json" "$run_dir/tool-versions/freecom-timestamp.json" 2>/dev/null; then :; fi
                if docker cp "$container_id:/output/freecom-watcomc.cfg" "$run_dir/tool-versions/freecom-watcomc.cfg" 2>/dev/null; then :; fi
            fi
            docker rm "$container_id" >/dev/null
            printf 'removed failed container %s\n' "$container_id" >&2
            finish_container_records "$run_id"
            return 1
        fi
        copy_output "$container_id" "$run_dir" "$component"
        docker rm "$container_id" >/dev/null
    done
    finish_container_records "$run_id"
    python3 tools/m01/collect_artifacts.py \
        --repo-root "$M01_ROOT" \
        --run-dir "$run_dir" \
        --contract "$M01_CONTRACT" \
        --toolchains "$M01_TOOLCHAIN_LOCK" \
        --source-archives "$M01_RUNTIME_ROOT/source-archives.json" \
        --output "$run_dir/manifest.json"
}

build() {
    assert_prestart_lifecycle_policy
    docker image inspect "$M01_IMAGE_TAG" >/dev/null 2>&1 || fail "M01 image is not available; run make m01-image"
    validate_gitlinks
    validate_contract_inputs
    [ ! -d "$M01_RESULTS_ROOT/run-1" ] || fail "run-1 exists; use m01-clean before rebuilding"
    [ ! -d "$M01_RESULTS_ROOT/run-2" ] || fail "run-2 exists; use m01-clean before rebuilding"
    mkdir -p "$M01_SOURCE_ROOT" "$M01_RUNTIME_ROOT"
    M01_RESOLVED_LOCAL_IMAGE_CONFIG_ID=$(docker image inspect "$M01_IMAGE_TAG" --format '{{.Id}}')
    validate_sha256_identity resolved_local_image_config_id "$M01_RESOLVED_LOCAL_IMAGE_CONFIG_ID"
    local fdkernel_sha freecom_sha country_sha
    fdkernel_sha=$(archive_component fdkernel fdkernel.tar "$(locked_component_commit components/fdkernel)")
    freecom_sha=$(archive_component freecom freecom.tar "$(locked_component_commit components/freecom)")
    country_sha=$(archive_component country country.tar "$(locked_component_commit components/country)")
    python3 - "$M01_RUNTIME_ROOT/source-archives.json" "$fdkernel_sha" "$freecom_sha" "$country_sha" <<'PY'
import json
import sys
from pathlib import Path

data = {"country": sys.argv[4], "fdkernel": sys.argv[2], "freecom": sys.argv[3]}
with Path(sys.argv[1]).open("w", encoding="utf-8", newline="\n") as stream:
    json.dump(data, stream, indent=2, sort_keys=True)
    stream.write("\n")
PY
    run_one run-1
    run_one run-2
    printf 'M01 two-run build completed\n'
}

compare() {
    python3 tools/m01/compare_runs.py \
        --run1 "$M01_RESULTS_ROOT/run-1" \
        --run2 "$M01_RESULTS_ROOT/run-2" \
        --output "$M01_RESULTS_ROOT/comparison.json"
}

enroll() {
    python3 tools/m01/enroll_m01_golden.py \
        --run1 "$M01_RESULTS_ROOT/run-1" \
        --run2 "$M01_RESULTS_ROOT/run-2" \
        --comparison "$M01_RESULTS_ROOT/comparison.json" \
        --golden "$M01_ROOT/qa/golden/m01-baseline.json"
}

verify() {
    python3 tools/m01/verify_m01.py --repo-root "$M01_ROOT"
}

clean() {
    if [ -e "$M01_RESULTS_ROOT" ]; then
        remove_recorded_container "$M01_RUNTIME_ROOT/image-probe-container.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-1/.container-fdkernel.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-1/.container-freecom.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-1/.container-country.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-2/.container-fdkernel.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-2/.container-freecom.json"
        remove_recorded_container "$M01_RESULTS_ROOT/run-2/.container-country.json"
        local resolved
        resolved=$(CDPATH= cd -- "$M01_RESULTS_ROOT" && pwd)
        case "$resolved" in
            "$M01_ROOT"/qa/results/m01) ;;
            *) fail "refusing to clean unexpected path: $resolved" ;;
        esac
        printf 'removing documented ignored M01 output directory: %s\n' "$resolved"
        python3 - "$resolved" "$M01_ROOT" <<'PY'
import shutil
import sys
from pathlib import Path

target = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()
if target != root / "qa/results/m01" or root not in target.parents or target.name != "m01":
    raise SystemExit("refusing to remove an unexpected path")
shutil.rmtree(target)
PY
    else
        printf '%s\n' 'M01 output directory does not exist; nothing to clean.'
    fi
}

case "${1-}" in
    preflight) preflight ;;
    image) image ;;
    build) build ;;
    compare) compare ;;
    enroll) enroll ;;
    verify) verify ;;
    clean) clean ;;
    *) printf '%s\n' 'Usage: build_baseline.sh {preflight|image|build|compare|enroll|verify|clean}' >&2; exit 64 ;;
esac
