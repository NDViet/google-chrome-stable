import requests
from bs4 import BeautifulSoup
import re
import yaml

# URL of the directory containing .deb files
url = "https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable"

# Fetch the HTML content of the directory
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find all .deb files
deb_files = [a['href'] for a in soup.find_all('a', href=True) if a['href'].endswith('.deb')]

# Dictionary to store the latest minor version for each major version
latest_versions = {}

# Set of package versions that ship an arm64 build
arm64_versions = set()

# Regular expressions to extract version numbers per architecture
amd64_pattern = re.compile(r'google-chrome-stable_(\d+\.\d+\.\d+\.\d+-\d+)_amd64\.deb')
arm64_pattern = re.compile(r'google-chrome-stable_(\d+\.\d+\.\d+\.\d+-\d+)_arm64\.deb')

def extract_version_parts(version):
    # Assuming the version format is 'major.minor.patch-build'
    # This function extracts the 'major.minor.patch' part
    if '-' in version:
        return version.split('-')[0]
    return version

def compare_versions(version1, version2):
    parts1 = extract_version_parts(version1)
    parts2 = extract_version_parts(version2)

    if parts1 is None or parts2 is None:
        return False

    parts1 = parts1.split('.')
    parts2 = parts2.split('.')

    for part1, part2 in zip(parts1, parts2):
        if int(part1) > int(part2):
            return True
        elif int(part1) < int(part2):
            return False
    return False

def platforms_for(package_version):
    # Every archived version ships amd64; arm64 is added only when Google
    # published an arm64 build for that exact package version.
    if package_version in arm64_versions:
        return "linux/amd64,linux/arm64"
    return "linux/amd64"

for deb_file in deb_files:
    arm64_match = arm64_pattern.search(deb_file)
    if arm64_match:
        arm64_versions.add(arm64_match.group(1))

    match = amd64_pattern.search(deb_file)
    if match:
        package_version = match.group(1)  # Extracted version part (e.g., 133.0.6943.126-1)
        major_version = package_version.split('.')[0]  # Extract major version (e.g., 133)

        # Update the latest version for the major version
        if major_version not in latest_versions or compare_versions(package_version, latest_versions[major_version]):
            latest_versions[major_version] = package_version

# Function to write results to a YAML file
def write_to_yaml(latest_versions, filename="browser-matrix.yml"):
    # Prepare the data structure for YAML
    yaml_data = {
        "matrix": {
            "browser": {
                major_version: {
                    "CHROME_VERSION": f"google-chrome-stable={package_version}",
                    "CHROME_PACKAGE_VERSION": package_version,
                    "CHROME_PLATFORMS": platforms_for(package_version)
                }
                for major_version, package_version in sorted(latest_versions.items(), key=lambda item: int(item[0]), reverse=True)
            }
        }
    }

    # Write to YAML file
    with open(filename, "w") as file:
        yaml.dump(yaml_data, file, default_flow_style=False, sort_keys=False)

    print(f"Results written to {filename}")

# Print the latest minor version for each major version
for major_version, latest_minor_version in sorted(latest_versions.items(), key=lambda item: int(item[0]), reverse=True):
    print(f"Latest version for {major_version}: {latest_minor_version} ({platforms_for(latest_minor_version)})")

# Write results to YAML file
write_to_yaml(latest_versions)
