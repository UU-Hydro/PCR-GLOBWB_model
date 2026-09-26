#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

DATA_DIR="$REPO_ROOT/tests/data/CATALOGUE/TEST_CASES/tugela"
OUTPUT_DIR="$REPO_ROOT/output/offline_pcrglobwb_qualloc/5arcminutes"
CLONE_MAP="clone_maps/tugela_5arcminutes.clone.map"

# Step 1 writes the daily totals step 2 reads, so both steps must agree on this.
PCRGLOBWB_OUTPUT_DIR="$REPO_ROOT/output/pcrglobwb/5arcminutes"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_5arcminutes.ini" \
    --output-dir "$PCRGLOBWB_OUTPUT_DIR" \
    --input-dir "$DATA_DIR" \
    --clone-map "$CLONE_MAP"

# step 2: QUAlloc on that output. Nothing it decides reaches PCR-GLOBWB.
pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    qualloc-run "$CONFIG_DIR/qualloc_5arcminutes.cfg" \
    --output-dir "$OUTPUT_DIR" \
    --input-dir "$DATA_DIR" \
    --clone-map "$CLONE_MAP" \
    --pcrglobwb-output-dir "$PCRGLOBWB_OUTPUT_DIR"
