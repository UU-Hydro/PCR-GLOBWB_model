#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

DATA_DIR="/path/to/input/"
OUTPUT_DIR="/path/to/output"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$CONFIG_DIR/default_5arcminutes.ini" \
    -mod "$OUTPUT_DIR" \
    -sd 2000-01-01 \
    -ed 2000-01-04 \
    -num_of_sp_years 0 \
    -clonemap clone_maps/tugela_5arcminutes.clone.map \
    -pff forcing/w5e5/pr_1979-2019_mm_per_day.nc \
    -tff forcing/w5e5/tas_1979-2019.nc \
    -rpetff forcing/w5e5/refPotEvap_1979-2019.nc
