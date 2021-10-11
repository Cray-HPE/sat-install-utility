#!/bin/bash
# (C) Copyright 2021 Hewlett Packard Enterprise Development LP.

base_dir=$(dirname "$0")
source sat-install-utility-venv/bin/activate
$base_dir/runUnitTest.sh
