# Copyright 2021 Hewlett Packard Enterprise Development LP
#
# Dockerfile for sat_install_utility

FROM arti.dev.cray.com/baseos-docker-master-local/alpine:3.13.5

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

COPY CHANGELOG.md README.md /sat/
COPY setup.py /sat/
COPY requirements.lock.txt /sat/requirements.txt
COPY tools /sat/tools
COPY sat_install_utility /sat/sat_install_utility
COPY docker_scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# TODO(CRAYSAT-1126): Remove PIP_EXTRA_INDEX_URL and PIP_TRUSTED_HOST
# From within the build context, 'host.docker.internal' means the host
# running Docker, i.e. 'localhost'. This is used to pull in dependencies
# that are not yet available on artifactory.
# See: https://connect.us.cray.com/confluence/x/n54cDQ
RUN apk update && apk add --no-cache python3 git bash && \
    python3 -m venv $VIRTUAL_ENV && \
    pip install --no-cache-dir -U pip && \
    PIP_EXTRA_INDEX_URL=http://host.docker.internal:8080 \
    PIP_TRUSTED_HOST="host.docker.internal" \
    pip install --no-cache-dir /sat/ && \
    rm -rf /sat/

ENTRYPOINT ["/entrypoint.sh"]
