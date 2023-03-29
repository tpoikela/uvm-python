#!/usr/bin/env python

import argparse
import os
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--production', action='store_true')
parser.add_argument('--clean', action='store_true')
args = parser.parse_args()

if args.clean:
    if os.path.isdir('./dist'):
        subprocess.run(['rm', 'dist/*'], check=True, shell=True)

build_cmd = 'python -m build'
testpypi_twine_cmd = 'python -m twine upload --repository testpypi dist/*'
production_twine_cmd = 'python -m twine upload dist/*'
twine_cmd = testpypi_twine_cmd if not args.production else production_twine_cmd

try:
    subprocess.run(build_cmd, check=True, shell=True)
    subprocess.run(twine_cmd, check=True, shell=True)
except subprocess.CalledProcessError:
    raise SystemExit(f'{build_cmd} failed. Not uploading to PyPi')

