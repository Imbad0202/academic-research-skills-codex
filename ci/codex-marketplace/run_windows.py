"""Run a pinned Codex patch on a disposable native Windows x64 CI VM."""

import ctypes
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time


NATIVE_TEST = (
    "marketplace_upgrade::tests::"
    "locked_destination_failure_cleans_checkout_and_throttles_next_upgrade"
)
RESULT_PATTERN = re.compile(
    r"^test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored;",
    re.MULTILINE,
)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked(args, cwd):
    return subprocess.check_output(
        args, cwd=cwd, text=True, encoding="utf-8", errors="replace"
    ).strip()


def file_system(path):
    # Query the actual temporary-file volume used by Rust's tempfile crate.
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_root = kernel.GetVolumePathNameW
    get_root.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
    get_root.restype = wintypes.BOOL
    root = ctypes.create_unicode_buffer(32768)
    if not get_root(str(path), root, len(root)):
        raise ctypes.WinError(ctypes.get_last_error())
    get_info = kernel.GetVolumeInformationW
    get_info.argtypes = [
        wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(wintypes.DWORD), wintypes.LPWSTR, wintypes.DWORD,
    ]
    get_info.restype = wintypes.BOOL
    name = ctypes.create_unicode_buffer(256)
    if not get_info(root.value, None, 0, None, None, None, name, len(name)):
        raise ctypes.WinError(ctypes.get_last_error())
    return {"volume": root.value, "file_system": name.value}


def cargo_test(label, selector, extra, checkout, results, receipt):
    args = [
        "cargo", "test", "--locked", "-p", "codex-core-plugins", selector,
        "--", "--test-threads=1", *extra,
    ]
    log = results / f"{label}.log"
    start = time.monotonic()
    print(f"Running {label}: {' '.join(args)}", flush=True)
    with log.open("w", encoding="utf-8", buffering=1) as stream:
        process = subprocess.Popen(
            args, cwd=checkout / "codex-rs", stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
        )
        for line in process.stdout:
            stream.write(line)
            print(line, end="", flush=True)
        code = process.wait()
    output = log.read_text(encoding="utf-8")
    totals = [tuple(map(int, match)) for match in RESULT_PATTERN.findall(output)]
    passed = sum(item[0] for item in totals)
    receipt["tests"][label] = {
        "command": args, "exit_code": code,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "passed": passed, "summaries": totals, "log_sha256": sha256(log),
    }
    if code != 0 or not totals or any(failed for _, failed, _ in totals):
        raise RuntimeError(f"{label} failed; see {log.name}")
    return output, passed


def main():
    package = Path(__file__).resolve().parent
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    checkout = workspace / "codex"
    results = workspace / "results"
    results.mkdir(exist_ok=True)
    receipt = {
        "status": "started", "platform": platform.platform(),
        "machine": platform.machine(), "python": platform.python_version(),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "validation_commit": os.environ.get("GITHUB_SHA"),
        "tests": {},
        "scope": "Filtered marketplace tests and a native Windows directory-sharing-lock test",
        "limitations": [
            "Windows Server 2022 VM, not the reporter's Windows 10 installation",
            "Sharing-lock rename failure does not reproduce every OS error 5 cause",
            "No installed desktop application or full Codex suite validation",
        ],
    }
    try:
        if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
            raise RuntimeError("Requires native Windows x64")
        receipt.update({
            "windows_edition": platform.win32_edition(),
            "windows_build": sys.getwindowsversion().build,
            "runner_image_os": os.environ.get("ImageOS"),
            "runner_image_version": os.environ.get("ImageVersion"),
            "python_executable": sys.executable,
        })
        # Give the regression tests an explicit, separate temporary directory.
        test_temp = workspace / "marketplace-test-temp"
        test_temp.mkdir(exist_ok=True)
        os.environ["TEMP"] = str(test_temp)
        os.environ["TMP"] = str(test_temp)
        tempfile.tempdir = None
        receipt["temporary_volume"] = file_system(Path(tempfile.gettempdir()))
        if receipt["temporary_volume"]["file_system"] != "NTFS":
            raise RuntimeError("The Windows sharing-lock test requires an NTFS test volume")
        receipt["free_bytes_before"] = shutil.disk_usage(workspace).free
        manifest = json.loads((package / "manifest.json").read_text())
        receipt["prior_evidence_manifest"] = manifest
        actual_base = checked(["git", "rev-parse", "HEAD"], checkout)
        receipt["actual_base_commit"] = actual_base
        if actual_base != manifest["base_commit"]:
            raise RuntimeError("Codex base commit mismatch")
        if checked(["git", "status", "--porcelain"], checkout):
            raise RuntimeError("Codex checkout must be clean before applying the patch")
        patch = package / "codex-marketplace-retry.patch"
        if sha256(patch) != manifest["patch_sha256"]:
            raise RuntimeError("Patch hash mismatch")
        subprocess.run(["git", "apply", "--check", str(patch)], cwd=checkout, check=True)
        subprocess.run(["git", "apply", str(patch)], cwd=checkout, check=True)
        for relative, expected in manifest["files"].items():
            if sha256(checkout / relative) != expected:
                raise RuntimeError(f"Patched source hash mismatch: {relative}")
        receipt["source_verified"] = True
        receipt["git"] = checked(["git", "--version"], checkout)
        receipt["rustc"] = checked(["rustc", "--version", "--verbose"], checkout / "codex-rs")
        receipt["cargo"] = checked(["cargo", "--version"], checkout / "codex-rs")
        if "rustc 1.99.1 " not in receipt["rustc"] or "host: x86_64-pc-windows-msvc" not in receipt["rustc"]:
            raise RuntimeError("Unexpected Rust version or host target")
        output, count = cargo_test(
            "native-sharing-lock", NATIVE_TEST, ["--exact"], checkout, results, receipt
        )
        if count != 1 or f"test {NATIVE_TEST} ... ok" not in output:
            raise RuntimeError("The Windows-only regression must run and pass exactly once")
        _, count = cargo_test("marketplace-all", "marketplace_", [], checkout, results, receipt)
        if count < 100:
            raise RuntimeError("Unexpectedly small marketplace test set; investigate filtering")
        receipt["status"] = "passed"
    except BaseException as error:
        receipt["status"] = "failed"
        receipt["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        receipt["free_bytes_after"] = shutil.disk_usage(workspace).free
        (results / "receipt.json").write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
