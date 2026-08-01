"""Fetch an arm64 ChromeDriver from Debian and package it for a release.

Google does not publish a linux/arm64 ChromeDriver (neither the legacy endpoint
nor Chrome for Testing). Debian, however, ships a `chromium-driver` binary
package built for arm64. This script resolves a Debian `chromium-driver` arm64
package whose upstream version matches the requested Chrome major version (via
snapshot.debian.org), downloads it, extracts the `chromedriver` binary and zips
it as `chromedriver_<chrome_version>_arm64.zip`.

ChromeDriver requires its major version to match the browser's major version, so
only a matching-major driver is packaged. When Debian has no matching build yet
the script exits 0 without producing a zip and the caller simply skips
archiving; a later run picks it up once Debian catches up.

Usage: python3 fetch_debian_chromedriver.py <chrome_version> <output_dir>
  <chrome_version> e.g. 151.0.7922.71-1 (the deb revision suffix is ignored)
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

SNAPSHOT = "https://snapshot.debian.org"
SRC_PACKAGE = "chromium"
BIN_PACKAGE = "chromium-driver"
TIMEOUT = 120
# How many matching-major source versions to probe (newest first).
MAX_CANDIDATES = 8


def log(message):
    print(message, flush=True)


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "google-chrome-stable-archiver"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.load(response)


def http_download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "google-chrome-stable-archiver"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response, open(dest, "wb") as out:
        while True:
            chunk = response.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)


def upstream_key(version):
    """Sort key from the leading numeric dotted upstream version.

    e.g. "151.0.7922.71-1~deb13u1" -> (151, 0, 7922, 71)
    """
    head = re.split(r"[-~+]", version, 1)[0]
    parts = []
    for piece in head.split("."):
        digits = re.match(r"\d+", piece)
        parts.append(int(digits.group()) if digits else 0)
    return tuple(parts)


def matching_source_versions(major):
    data = http_json(f"{SNAPSHOT}/mr/package/{SRC_PACKAGE}/")
    versions = [entry["version"] for entry in data.get("result", [])]
    matching = [v for v in versions if upstream_key(v)[:1] == (major,)]
    matching.sort(key=upstream_key, reverse=True)
    log(f"Debian {SRC_PACKAGE} versions matching major {major}: {matching or 'none'}")
    return matching[:MAX_CANDIDATES]


def arm64_driver_file(source_version):
    """Return (deb_filename, download_url) for the arm64 chromium-driver, or None."""
    # Resolve the binary package version produced by this source version.
    bin_version = source_version
    try:
        binpkgs = http_json(
            f"{SNAPSHOT}/mr/package/{SRC_PACKAGE}/{source_version}/binpackages"
        )
        for entry in binpkgs.get("result", []):
            if entry.get("name") == BIN_PACKAGE:
                bin_version = entry.get("version", source_version)
                break
    except Exception as exc:  # noqa: BLE001 - best effort, fall back to source version
        log(f"  binpackages lookup failed ({exc}); assuming version {bin_version}")

    binfiles = http_json(
        f"{SNAPSHOT}/mr/binary/{BIN_PACKAGE}/{bin_version}/binfiles?fileinfo=1"
    )
    fileinfo = binfiles.get("fileinfo", {})
    for entry in binfiles.get("result", []):
        if entry.get("architecture") != "arm64":
            continue
        file_hash = entry.get("hash")
        infos = fileinfo.get(file_hash, [])
        name = infos[0]["name"] if infos else f"{BIN_PACKAGE}_{bin_version}_arm64.deb"
        return name, f"{SNAPSHOT}/file/{file_hash}"
    return None


def extract_chromedriver(deb_path, work_dir):
    extract_dir = os.path.join(work_dir, "extract")
    os.makedirs(extract_dir, exist_ok=True)
    subprocess.run(["dpkg-deb", "-x", deb_path, extract_dir], check=True)
    for root, _dirs, files in os.walk(extract_dir):
        if "chromedriver" in files:
            return os.path.join(root, "chromedriver")
    raise FileNotFoundError("chromedriver binary not found inside the Debian package")


def package(chrome_version, output_dir):
    major = upstream_key(chrome_version)[0]
    log(f"Resolving Debian arm64 chromium-driver for Chrome major {major}...")

    resolved = None
    for source_version in matching_source_versions(major):
        try:
            found = arm64_driver_file(source_version)
        except Exception as exc:  # noqa: BLE001
            log(f"  {source_version}: lookup failed ({exc})")
            continue
        if found:
            resolved = (source_version, *found)
            break
        log(f"  {source_version}: no arm64 binary file")

    if not resolved:
        log(f"No matching-major arm64 chromium-driver found on Debian for {chrome_version}; skipping.")
        return None

    source_version, deb_name, url = resolved
    log(f"Using Debian {deb_name} ({url})")

    with tempfile.TemporaryDirectory() as work_dir:
        deb_path = os.path.join(work_dir, deb_name)
        http_download(url, deb_path)
        driver_path = extract_chromedriver(deb_path, work_dir)

        os.makedirs(output_dir, exist_ok=True)
        zip_path = os.path.join(output_dir, f"chromedriver_{chrome_version}_arm64.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Store as chromedriver-linux-arm64/chromedriver, mirroring the
            # Chrome for Testing archive layout.
            info = zipfile.ZipInfo("chromedriver-linux-arm64/chromedriver")
            info.external_attr = 0o755 << 16  # executable
            with open(driver_path, "rb") as fh:
                zf.writestr(info, fh.read())

    version_path = os.path.join(output_dir, "chromedriver_arm64.version")
    with open(version_path, "w") as fh:
        fh.write(source_version)

    log(f"Packaged {zip_path} (Debian chromium-driver {source_version}).")
    return zip_path


if __name__ == "__main__":
    chrome_version = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    try:
        package(chrome_version, output_dir)
    except Exception as exc:  # noqa: BLE001 - never fail the archive job on driver issues
        log(f"::warning::Failed to fetch Debian arm64 ChromeDriver: {exc}")
        sys.exit(0)
