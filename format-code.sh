#!/bin/bash

shopt -s globstar

# Format all Python code
black --line-length 79 --py36 *.py pykzee/**/*.py

# Run flake8
flake8 *.py pykzee/**/*.py

# Format JavaScript code
cd js
node_modules/.bin/prettier --write --config .prettierrc \
  *.js *.json .prettierrc src/**/*.{js,svelte,css}
