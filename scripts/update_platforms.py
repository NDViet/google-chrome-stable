import yaml
import sys


def update_platforms(version, platforms):
    """Set CHROME_PLATFORMS for the matrix entry of the given version.

    ``platforms`` is derived from the packages actually archived to the
    release (e.g. "linux/amd64" or "linux/amd64,linux/arm64"), so the matrix
    reflects real per-version architecture support regardless of when each
    architecture becomes available.
    """
    major_version = version.split('.')[0]
    with open('browser-matrix.yml', 'r') as file:
        data = yaml.safe_load(file)

    browser = data['matrix']['browser']
    if major_version not in browser:
        # Nothing to annotate if the version was never recorded.
        print(f"Version {version} not found in matrix; skipping.")
        return

    current = browser[major_version].get('CHROME_PLATFORMS')
    if current == platforms:
        print(f"CHROME_PLATFORMS for {version} already {platforms}; no change.")
        return

    browser[major_version]['CHROME_PLATFORMS'] = platforms

    with open('browser-matrix.yml', 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)
    print(f"Set CHROME_PLATFORMS for {version} to {platforms}.")


if __name__ == "__main__":
    version = sys.argv[1]
    platforms = sys.argv[2]
    update_platforms(version, platforms)
