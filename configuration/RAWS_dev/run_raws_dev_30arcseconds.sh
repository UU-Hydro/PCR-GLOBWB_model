#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../.." && pwd)"

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
DATA_CATALOGUE_DIR=/scratch/depfg/7006713/temp/quick_commit/RAWS/RAWS_data_catalogue/CATALOGUE/TEST_CASES/
DATA_DIR="${REPO_ROOT}/../data"

START_DATE=2000-01-01
END_DATE=2000-01-07

INPUT_DIR="$DATA_DIR/CATALOGUE/TEST_CASES/rhine"
CLONE_MAP="clone_maps/sub_basins/30arcseconds/rhine_30arcseconds_1_1"

# ---------------------------------------------------------------------------
# get data
# ---------------------------------------------------------------------------
mkdir -p "$DATA_DIR/CATALOGUE"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    rsync -avh --delete --partial --info=progress2 \
    "eejit:${DATA_CATALOGUE_DIR%/}" "$DATA_DIR/CATALOGUE"

# ---------------------------------------------------------------------------
# 1/2 PCR-GLOBWB on its own
# ---------------------------------------------------------------------------
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_30arcseconds.ini" \
    -mod "$DATA_DIR/output/30arcseconds/pcrglobwb" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -sd "$START_DATE" \
    -ed "$END_DATE"

# ---------------------------------------------------------------------------
# 2/2 QUAlloc stepped from inside PCR-GLOBWB
# ---------------------------------------------------------------------------
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/online_pcrglobwb_qualloc_30arcseconds.ini" \
    -mod "$DATA_DIR/output/30arcseconds/online_pcrglobwb_qualloc" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -sd "$START_DATE" \
    -ed "$END_DATE" \
    -qcf "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/qualloc_30arcseconds.cfg"
