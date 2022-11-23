#
# MIT License
#
# (C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Dockerfile for sat_install_utility

FROM artifactory.algol60.net/csm-docker/stable/docker.io/library/alpine:3.15

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY CHANGELOG.md README.md /sat/
COPY setup.py /sat/
COPY requirements.lock.txt /sat/requirements.txt
COPY tools /sat/tools
COPY sat_install_utility /sat/sat_install_utility
COPY docker_scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# For external dependencies, always pull from internal-pip-stable-local

# TODO: stop pulling from internal artifactory when nexusctl is open source.
ARG PIP_EXTRA_INDEX_URL="https://arti.hpc.amslabs.hpecorp.net/artifactory/internal-pip-stable-local/ \
    https://artifactory.algol60.net/artifactory/csm-python-modules/simple"

RUN --mount=type=secret,id=netrc,target=/root/.netrc \
    apk update && apk add --no-cache python3 git bash && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir /sat/ && \
    rm -rf /sat/

ENTRYPOINT ["/entrypoint.sh"]
