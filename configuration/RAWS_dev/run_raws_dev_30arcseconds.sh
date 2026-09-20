#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../.." && pwd)"

# ---------------------------------------------------------------------------
# settings
# ---------------------------------------------------------------------------
DATA_CATALOGUE_DIR=/scratch/depfg/7006713/temp/quick_commit/RAWS/RAWS_data_catalogue/CATALOGUE/TEST_CASES/
DATA_DIR="/Users/7006713/Desktop/code/raws_data_catalogue/data"

INPUT_DIR="$DATA_DIR/CATALOGUE/TEST_CASES/tugela"
CLONE_MAP="clone_maps/tugela_30arcseconds.clone.map"

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
echo "=== 1/3 pcrglobwb"
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_30arcseconds.ini" \
    -mod "$DATA_DIR/output/30arcseconds/pcrglobwb" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP"

# # ---------------------------------------------------------------------------
# # 2/3 QUAlloc on the reported PCR-GLOBWB output
# # ---------------------------------------------------------------------------
echo "=== 2/3 offline_pcrglobwb_qualloc"
-pcrglobwb_mod points at the daily totals step 1/3 reported, so the three sets
share one PCR-GLOBWB trajectory and that run is not repeated here
pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    python -m qualloc.qualloc_runner \
    "$REPO_ROOT/configuration/run_with_args/offline_pcrglobwb_qualloc/qualloc_30arcseconds.cfg" \
    -mod "$DATA_DIR/output/30arcseconds/offline_pcrglobwb_qualloc" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -pcrglobwb_mod "$DATA_DIR/output/30arcseconds/pcrglobwb"

# # ---------------------------------------------------------------------------
# # 3/3 QUAlloc stepped from inside PCR-GLOBWB
# # ---------------------------------------------------------------------------
# echo "=== 3/3 online_pcrglobwb_qualloc"
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/online_pcrglobwb_qualloc_30arcseconds.ini" \
    -mod "$DATA_DIR/output/30arcseconds/online_pcrglobwb_qualloc" \
    -mid "$INPUT_DIR" \
    -clonemap "$CLONE_MAP" \
    -qcf "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/qualloc_30arcseconds.cfg"
