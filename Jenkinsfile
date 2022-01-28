// vi: sts=4 et ai
// (C) Copyright 2021 Hewlett Packard Enterprise Development LP.

@Library('dst-shared@release/sat-2.2') _

dockerBuildPipeline {
  repository = "cray"
  app = "sat-install-utility"
  name = "sat-install-utility"
  description = "System Admin Toolkit Install Utility"
  dockerfile = "Dockerfile"
  product = "sat"
  buildPrepScript = "build_scripts/runBuildPrepVenv.sh"
  unitTestScript = "build_scripts/runUnitTestVenv.sh"
  versionScript = "build_scripts/version.sh"
}
