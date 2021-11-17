#!/bin/bash
# (C) Copyright 2021 Hewlett Packard Enterprise Development LP.
PIP_EXTRA_INDEX_URL="https://arti.dev.cray.com/artifactory/internal-pip-master-local/ \
    https://arti.dev.cray.com/artifactory/csm-python-modules-remote/simple" \
pip3 install -r requirements-dev.lock.txt
