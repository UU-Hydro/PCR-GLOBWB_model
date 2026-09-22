#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    pcrglobwb-run "$REPO_ROOT/configuration/run/pcrglobwb/pcrglobwb_30arcseconds.ini"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" \
    python -m qualloc.qualloc_runner "$CONFIG_DIR/qualloc_30arcseconds.cfg"
