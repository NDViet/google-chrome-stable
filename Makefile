install_dependencies:
	python3 -m pip install -r ./scripts/requirements.txt

extract_versions:
	python3 scripts/extract_versions.py

read_versions:
	python3 scripts/read_versions.py