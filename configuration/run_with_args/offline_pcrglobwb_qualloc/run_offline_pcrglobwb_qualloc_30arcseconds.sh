#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

DATA_DIR="$REPO_ROOT/tests/data/CATALOGUE/TEST_CASES/tugela"
OUTPUT_DIR="$REPO_ROOT/output/offline_pcrglobwb_qualloc/30arcseconds"
CLONE_MAP="clone_maps/tugela_30arcseconds.clone.map"

# Step 1 writes the daily totals step 2 reads, so both steps must agree on this.
PCRGLOBWB_OUTPUT_DIR="$REPO_ROOT/output/pcrglobwb/30arcseconds"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_30arcseconds.ini" \
    -mod "$PCRGLOBWB_OUTPUT_DIR" \
    -mid "$DATA_DIR" \
    -clonemap "$CLONE_MAP"

# step 2: QUAlloc on that output. Nothing it decides reaches PCR-GLOBWB.
pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    python -m qualloc.qualloc_runner "$CONFIG_DIR/qualloc_30arcseconds.cfg" \
    -mod "$OUTPUT_DIR" \
    -mid "$DATA_DIR" \
    -clonemap "$CLONE_MAP" \
    -pcrglobwb_mod "$PCRGLOBWB_OUTPUT_DIR"
