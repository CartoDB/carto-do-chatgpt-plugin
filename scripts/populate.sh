#!/bin/bash

cd process_json || exit
poetry run python -m process_json --class_name=DODataset --filepath=data/geographies.json
poetry run python -m process_json --class_name=DODataset --filepath=data/datasets.json
poetry run python -m process_json --class_name=DOVariable --filepath=data/variables.json
