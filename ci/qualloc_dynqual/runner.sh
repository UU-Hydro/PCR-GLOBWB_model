
#!/bin/bash

set -euo pipefail

env_dir="$(pwd)/environment"
env_dir=$(mktemp -d)
config_dir="$(pwd)/configuration"
model_dir="$(pwd)/../../model"
eval_file="$(pwd)/evaluate.py"

echo "## Configuration ##
  env_dir: $env_dir
  config_dir: $config_dir
  model_dir: $model_dir
  eval_file: $eval_file"

echo "Creating conda environment..."
conda env create --file "environment.yml" --prefix "$env_dir"

echo "Creating configuration directory..."
mkdir -p "$config_dir"
cp configuration.ini "$config_dir/configuration.ini"
sed -i "s|{ci_input_dir}|$(pwd)/data/input|g" "$config_dir/configuration.ini"
sed -i "s|{ci_output_dir}|$(pwd)/output|g" "$config_dir/configuration.ini"
sed -i "s|{ci_config_dir}|$config_dir|g" "$config_dir/configuration.ini"
cp configuration_qualloc.cfg "$config_dir/configuration_qualloc.cfg"
sed -i "s|{ci_input_dir}|$(pwd)/data/input|g" "$config_dir/configuration_qualloc.cfg"
sed -i "s|{ci_output_dir}|$(pwd)/output|g" "$config_dir/configuration_qualloc.cfg"

echo "Running model..."
export PCRASTER_NR_WORKER_THREADS=8
conda run --prefix "$env_dir" python "$model_dir/deterministic_runner.py" "$config_dir/configuration.ini"

echo "Evaluate output..."
conda run --prefix "$env_dir" python "$eval_file"
