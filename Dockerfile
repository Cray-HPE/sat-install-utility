# Copyright 2021 Hewlett Packard Enterprise Development LP
#
# Dockerfile for sat_install_utility

FROM arti.dev.cray.com/baseos-docker-master-local/alpine:3.13.2

COPY CHANGELOG.md README.md /sat/
COPY setup.py /sat/
COPY requirements.lock.txt /sat/requirements.txt
COPY tools /sat/tools
COPY sat_install_utility /sat/sat_install_utility
COPY docker_scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN apk update && apk add --no-cache python3 git bash && \
    python3 -m venv $VIRTUAL_ENV && \
    PIP_INDEX_URL=http://dst.us.cray.com/dstpiprepo/simple \
    PIP_TRUSTED_HOST=dst.us.cray.com \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir /sat/ && \
    rm -rf /sat/

ENTRYPOINT ["/entrypoint.sh"]
