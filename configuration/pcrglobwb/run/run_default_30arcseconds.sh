#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CONFIG_DIR/../../.." && pwd)"

pixi run --manifest-path "$REPO_ROOT/pixi.toml" pcrglobwb-run "$CONFIG_DIR/default_30arcseconds.ini"
