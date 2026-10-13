#!/usr/bin/env bash
# Runs every check in this repository and writes the results to output/.
# Needs Python 3 and Java 11 or later (HermiT and ROBOT run on Java).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p tools output
if [ ! -f tools/robot.jar ]; then
  curl -fsSL -o tools/robot.jar https://github.com/ontodev/robot/releases/download/v1.9.11/robot.jar
fi
python3 scripts/validate.py | tee output/validation-results.txt
python3 scripts/asof_query.py | tee output/asof_query_output.txt
