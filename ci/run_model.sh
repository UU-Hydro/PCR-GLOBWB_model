#!/bin/bash

CONDA_ENVIRONMENT=$1
if [ -z "$CONDA_ENVIRONMENT" ]; then
  echo "No conda environment provided. Please provide a conda environment as the first argument."
  exit 1
fi

CONFIGURATION_FILE=$2
if [ -z "$CONFIGURATION_FILE" ]; then
  echo "No configuration file provided. Please provide a configuration file as the second argument."
  exit 1
fi

temporary_directory="./ci/sample_data/temporary/"

configuration_subfile=$(sed "s+.*sample_data/++" <<< $CONFIGURATION_FILE)
configuration_temporary=$temporary_directory$configuration_subfile
echo $configuration_temporary

mkdir -p $(dirname $configuration_temporary)
cp $CONFIGURATION_FILE $configuration_temporary
sed -i "s+PWDTEMPLATE+$(pwd)+" $configuration_temporary

model_runner="./model/deterministic_runner.py"
conda run -n $CONDA_ENVIRONMENT python $model_runner $configuration_temporary
