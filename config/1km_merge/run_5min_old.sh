#!/usr/bin/env bash
set -euo pipefail

CONFIG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="$(cd "$CONFIG_DIR/../.." && pwd)"

cd "$MODEL_DIR"
set +u
eval "$(pixi shell-hook --shell bash)"
set -u

python model/deterministic_runner.py "$CONFIG_DIR/5min_old_cropped.ini"
