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
CLONE_MAP="clone_maps/tugela_30arcseconds.clone.map"

# log levels for all runs: DEBUG, INFO, WARNING, ERROR or CRITICAL
LOG_LEVEL=DEBUG
FILE_LEVEL=DEBUG

# ---------------------------------------------------------------------------
# get data
# ---------------------------------------------------------------------------
mkdir -p "$DATA_DIR/CATALOGUE"

# pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
#     rsync -avh --delete --partial --info=progress2 \
#     "eejit:${DATA_CATALOGUE_DIR%/}" "$DATA_DIR/CATALOGUE"

# ---------------------------------------------------------------------------
# 1/3 PCR-GLOBWB on its own
# ---------------------------------------------------------------------------
echo "=== 1/3 pcrglobwb"
pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
    "$REPO_ROOT/configuration/run_with_args/pcrglobwb/pcrglobwb_30arcseconds.ini" \
    --output-dir "$DATA_DIR/output/30arcseconds/pcrglobwb" \
    --input-dir "$INPUT_DIR" \
    --clone-map "$CLONE_MAP" \
    --log-level "$LOG_LEVEL" --file-level "$FILE_LEVEL"

# # ---------------------------------------------------------------------------
# # 2/3 QUAlloc on the reported PCR-GLOBWB output
# # ---------------------------------------------------------------------------
# echo "=== 2/3 offline_pcrglobwb_qualloc"
# pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
#     qualloc-run \
#     "$REPO_ROOT/configuration/run_with_args/offline_pcrglobwb_qualloc/qualloc_30arcseconds.cfg" \
#     --output-dir "$DATA_DIR/output/30arcseconds/offline_pcrglobwb_qualloc" \
#     --input-dir "$INPUT_DIR" \
#     --clone-map "$CLONE_MAP" \
#     --pcrglobwb-output-dir "$DATA_DIR/output/30arcseconds/pcrglobwb" \
#     --log-level "$LOG_LEVEL" --file-level "$FILE_LEVEL"

# # # ---------------------------------------------------------------------------
# # # 3/3 QUAlloc stepped from inside PCR-GLOBWB
# # # ---------------------------------------------------------------------------
# echo "=== 3/3 online_pcrglobwb_qualloc"
# pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run-with-arguments \
#     "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/online_pcrglobwb_qualloc_30arcseconds.ini" \
#     --output-dir "$DATA_DIR/output/30arcseconds/online_pcrglobwb_qualloc" \
#     --input-dir "$INPUT_DIR" \
#     --clone-map "$CLONE_MAP" \
#     --qualloc-config "$REPO_ROOT/configuration/run_with_args/online_pcrglobwb_qualloc/qualloc_30arcseconds.cfg" \
#     --log-level "$LOG_LEVEL" --file-level "$FILE_LEVEL"
