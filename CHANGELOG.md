# Changelog

(C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.1] - 2022-05-24

### Changed
- Made changes related to open sourcing of sat-install-utility.
    - Update Jenkinsfile to use csm-shared-library.
    - Add Makefile for building container image and helm chart.
    - Pull base container image from external location.

## [1.5.0] - 2022-04-06

### Changed

- Added support for HTTP authentication to Nexus by incrementing the minimum version
  of ``shasta-install-utility-common`` and the pinned versions of both ``nexusctl`` and
  ``shasta-install-utility-common``.

## [1.4.3] - 2022-02-16

### Changed

- Updated to use ``cfs-config-util`` 2.0.0 and updated the call to
  ``cfs_activate_version`` to pass arguments correctly for that new version.

### Removed

- Removed unused import of ``cfs_deactivate_version`` function.

## [1.4.2] - 2022-01-21

### Fixed

- Added missing dependencies to locked requirements files.

## [1.4.1] - 2022-01-05

### Changed

- Updated to new versions of ``cray-product-catalog`` and ``shasta-install-utility-common``.
  The updated version of ``cray-product-catalog`` no longer updates the "active" field
  by default when running ``catalog_update``, so ``shasta-install-utility-common`` is updated
  to a version that explicitly sets the "active" field.

## [1.4.0] - 2021-11-15

### Added

- When activating or uninstalling a version of SAT, the 'sat-ncn' layer of the
  CFS configuration(s) targeting nodes with the "Management" role and the
  "Master" subrole is now updated or removed automatically.

## [1.3.3] - 2021-11-15

### Added

- When activating a version of SAT, set it active in the product catalog.

## [1.3.2] - 2021-10-29

### Changed

- Use command-line parser from ``shasta-install-utility-common``,
  replacing ``get_parser``.

## [1.3.1] - 2021-10-13

### Changed

- Updated build pipeline to use internally-available library versions,
  and use new library name of ``shasta-install-utility-common``.

## [1.3.0] - 2021-09-03

### Changed

- Removed code common to all install utilities and added a dependency on
 ``install_utility_common``.
- Removed the product positional argument.
- Change expected product catalog data format.

## [1.2.0] - 2021-09-03

### Changed

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
