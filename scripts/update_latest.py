import yaml
import subprocess
import sys

def update_output_yaml(version):
    major_version = version.split('.')[0]
    with open('browser-matrix.yml', 'r') as file:
        data = yaml.safe_load(file)

    if major_version in data['matrix']['browser']:
        data['matrix']['browser'][major_version]['CHROME_VERSION'] = f'google-chrome-stable={version}'
        data['matrix']['browser'][major_version]['CHROME_PACKAGE_VERSION'] = version
    else:
        data['matrix']['browser'][major_version] = {
            'CHROME_VERSION': f'google-chrome-stable={version}',
            'CHROME_PACKAGE_VERSION': version
        }

    # Sort the dictionary by major_version as a number
    sorted_data = dict(sorted(data['matrix']['browser'].items(), key=lambda x: int(x[0]), reverse=True))
    data['matrix']['browser'] = sorted_data

    with open('browser-matrix.yml', 'w') as file:
        yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)

if __name__ == "__main__":
    version = sys.argv[1]
    update_output_yaml(version)