import yaml

def extract_versions_from_yaml(file_path):
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    versions = []
    for major_version, details in data['matrix']['browser'].items():
        versions.append(details['CHROME_PACKAGE_VERSION'])
    versions.reverse()

    versions_string = str(versions).replace(' ', '')
    return versions_string

file_path = 'browser-matrix.yml'
versions_string = extract_versions_from_yaml(file_path)
with open('.env', 'w') as file:
    file.write(f"OUTPUT_VERSIONS=\"{versions_string}\"")