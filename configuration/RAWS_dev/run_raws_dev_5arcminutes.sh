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

INPUT_DIR="$DATA_DIR/CATALOGUE/TEST_CASES/tugela"
CLONE_MAP="clone_maps/tugela_5arcminutes"

# ---------------------------------------------------------------------------
# get data
# ---------------------------------------------------------------------------
mkdir -p "$DATA_DIR/CATALOGUE"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    rsync -avh --delete --partial --info=progress2 \
    "eejit:${DATA_CATALOGUE_DIR%/}" "$DATA_DIR/CATALOGUE"

# ---------------------------------------------------------------------------
# 1/3 PCR-GLOBWB on its own
# ---------------------------------------------------------------------------
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_5arcminutes.ini" \
    -mod "$DATA_DIR/output/5arcminutes/pcrglobwb" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -sd "$START_DATE" \
    -ed "$END_DATE"

# ---------------------------------------------------------------------------
# 2/3 QUAlloc on the reported PCR-GLOBWB output
# ---------------------------------------------------------------------------
pixi run --manifest-path "$REPO_ROOT/pixi.toml" qualloc-run \
    "$REPO_ROOT/configuration/run_with_args/offline_pcrglobwb_qualloc/qualloc_5arcminutes.cfg" \
    -mod "$DATA_DIR/output/5arcminutes/offline_pcrglobwb_qualloc" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -sd "$START_DATE" \
    -ed "$END_DATE" \
    -pcrglobwb_mod "$DATA_DIR/output/5arcminutes/pcrglobwb"

# ---------------------------------------------------------------------------
# 3/3 QUAlloc stepped from inside PCR-GLOBWB
# ---------------------------------------------------------------------------
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/online_pcrglobwb_qualloc_5arcminutes.ini" \
    -mod "$DATA_DIR/output/5arcminutes/online_pcrglobwb_qualloc" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -sd "$START_DATE" \
    -ed "$END_DATE" \
    -qcf "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/qualloc_5arcminutes.cfg"
