# Changelog

(C) Copyright 2021 Hewlett Packard Enterprise Development LP.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Changed the expected format of data in the ``cray-product-catalog`` ConfigMap
  so that multiple Docker images can be associated with a single product
  version. Maintains backwards compatibility with previous ``cray-product-catalog``
  data format.
- Changed the behavior of the "activate" action from re-ordering group
  repository members to making the active product version's hosted repository
  the sole member of the group repository.

## [1.1.0] - 2021-07-26

### Added

- Added the ability to remove entries from the product catalog on an uninstall.

## [1.0.0] - 2021-07-19

### Added

- Added ``sat_install_utility`` Python package with support for downgrade and
  uninstall by interacting with the container image registry and package
  repositories.
- Added ``Dockerfile`` for building a ``sat-install-utility`` image, and
  ``Jenkinsfile`` for building the image in a Jenkins pipeline.
