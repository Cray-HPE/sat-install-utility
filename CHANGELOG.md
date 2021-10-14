# Changelog

(C) Copyright 2021 Hewlett Packard Enterprise Development LP.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.1] - 2021-10-13

### Changed

- Updated build pipeline to use internally-available library versions.

## [1.3.0] - 2021-09-03

### Changed

- Removed code common to all install utilities and added a dependency on
  `install_utility_common`.

## [1.2.0] - 2021-09-03

### Changed

- Removed the product positional argument.
- Refactored code that interacts with the product catalog in preparation for
  change to use a common install utility library.
- Change expected product catalog data format.
- Changed the expected format of data in the ``cray-product-catalog`` ConfigMap
  so that multiple Docker images can be associated with a single product
  version. Maintains backwards compatibility with previous ``cray-product-catalog``
  data format.
- Changed the behavior of the "activate" action from re-ordering group
  repository members to making the active product version's hosted repository
  the sole member of the group repository.

### Security

- Incremented version of Alpine Linux from 3.13.2 to 3.13.5 
  to address OpenSSL CVE-2021-3711.

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
