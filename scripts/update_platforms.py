import yaml
import sys


def update_platforms(version, platforms):
    """Set CHROME_PLATFORMS for the matrix entry of the given version.

    ``platforms`` is derived from the packages actually archived to the
    release (e.g. "linux/amd64" or "linux/amd64,linux/arm64"), so the matrix
    reflects real per-version architecture support regardless of when each
    architecture becomes available. The entry is created when the version is
    not recorded yet, so this can run standalone as well as after
    update_latest.py.
    """
    major_version = version.split('.')[0]
    with open('browser-matrix.yml', 'r') as file:
        data = yaml.safe_load(file)

    browser = data['matrix']['browser']

    if major_version in browser:
        entry = browser[major_version]
        if entry.get('CHROME_PLATFORMS') == platforms:
            print(f"CHROME_PLATFORMS for {version} already {platforms}; no change.")
            return
        entry['CHROME_PLATFORMS'] = platforms
        print(f"Set CHROME_PLATFORMS for {version} to {platforms}.")
    else:
        browser[major_version] = {
            'CHROME_VERSION': f'google-chrome-stable={version}',
            'CHROME_PACKAGE_VERSION': version,
            'CHROME_PLATFORMS': platforms
        }
        print(f"Added {version} with CHROME_PLATFORMS {platforms}.")

    # Keep the matrix sorted by major version, newest first.
    data['matrix']['browser'] = dict(
        sorted(browser.items(), key=lambda x: int(x[0]), reverse=True)
    )

    with open('browser-matrix.yml', 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    version = sys.argv[1]
    platforms = sys.argv[2]
    update_platforms(version, platforms)
