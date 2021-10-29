#!/bin/bash
# (C) Copyright 2021 Hewlett Packard Enterprise Development LP.

base_dir=$(dirname "$0")
rm -rf sat-install-utility-venv && virtualenv -p $(which python3) ./sat-install-utility-venv
source sat-install-utility-venv/bin/activate
$base_dir/runBuildPrep.sh
