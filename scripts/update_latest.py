import yaml
import sys
import requests

# Same pool used by extract_versions.py to discover published .deb packages.
POOL_URL = "https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable"


def has_arm64_build(version):
    """Return True when Google published an arm64 .deb for this exact version."""
    deb = f"google-chrome-stable_{version}_arm64.deb"
    try:
        response = requests.head(f"{POOL_URL}/{deb}", allow_redirects=True, timeout=30)
        return response.status_code == 200
    except requests.RequestException:
        return False


def platforms_for(version):
    if has_arm64_build(version):
        return "linux/amd64,linux/arm64"
    return "linux/amd64"


def update_output_yaml(version):
    major_version = version.split('.')[0]
    with open('browser-matrix.yml', 'r') as file:
        data = yaml.safe_load(file)

    platforms = platforms_for(version)

    if major_version in data['matrix']['browser']:
        data['matrix']['browser'][major_version]['CHROME_VERSION'] = f'google-chrome-stable={version}'
        data['matrix']['browser'][major_version]['CHROME_PACKAGE_VERSION'] = version
        data['matrix']['browser'][major_version]['CHROME_PLATFORMS'] = platforms
    else:
        data['matrix']['browser'][major_version] = {
            'CHROME_VERSION': f'google-chrome-stable={version}',
            'CHROME_PACKAGE_VERSION': version,
            'CHROME_PLATFORMS': platforms
        }

    # Sort the dictionary by major_version as a number
    sorted_data = dict(sorted(data['matrix']['browser'].items(), key=lambda x: int(x[0]), reverse=True))
    data['matrix']['browser'] = sorted_data

    with open('browser-matrix.yml', 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    version = sys.argv[1]
    update_output_yaml(version)
