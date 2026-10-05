#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../.." && pwd)"

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
DATA_CATALOGUE_DIR=/scratch/depfg/7006713/temp/quick_commit/RAWS/RAWS_data_catalogue/CATALOGUE/TEST_CASES/
DATA_DIR="${REPO_ROOT}/../data"

INPUT_DIR="$DATA_DIR/CATALOGUE/TEST_CASES/tugela"
CLONE_MAP="clone_maps/tugela_30arcminutes.clone.map"

# ---------------------------------------------------------------------------
# get data
# ---------------------------------------------------------------------------
mkdir -p "$DATA_DIR/CATALOGUE"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    rsync -avh --delete --partial --info=progress2 \
    "eejit:${DATA_CATALOGUE_DIR%/}" "$DATA_DIR/CATALOGUE"

# ---------------------------------------------------------------------------
# PCR-GLOBWB on its own (no QUAlloc inputs exist at 30 arcminutes)
# ---------------------------------------------------------------------------
echo "=== pcrglobwb"
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_30arcminutes.ini" \
    -mod "$DATA_DIR/output/30arcminutes/pcrglobwb" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP"
