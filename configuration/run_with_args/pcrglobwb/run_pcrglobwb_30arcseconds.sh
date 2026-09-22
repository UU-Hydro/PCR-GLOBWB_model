#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

DATA_DIR="$REPO_ROOT/tests/data/CATALOGUE/TEST_CASES/tugela"
OUTPUT_DIR="$REPO_ROOT/output/pcrglobwb/30arcseconds"
CLONE_MAP="clone_maps/tugela_30arcseconds.clone.map"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$CONFIG_DIR/pcrglobwb_30arcseconds.ini" \
    -mod "$OUTPUT_DIR" \
    -mid "$DATA_DIR" \
    -clonemap "$CLONE_MAP"
