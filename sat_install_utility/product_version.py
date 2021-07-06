"""
Contains the InstalledProductVersion class.

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
"""

import warnings

from kubernetes.config import load_kube_config, ConfigException
from kubernetes.client import CoreV1Api
from kubernetes.client.rest import ApiException
from nexusctl.docker.api import DockerApi
from nexusctl.common.rest import NexusCtlHttpError
from urllib3.exceptions import MaxRetryError
from yaml import safe_load, YAMLLoadWarning

from sat_install_utility.cached_property import cached_property


class InstalledProductVersion:
    """A representation of a version of a product that is currently installed.

    Attributes:
        name: The product name.
        version: The product version.
    """

    # TODO: override dist version?
    DIST = 'sle-15sp2'
    PRODUCT_CATALOG_CONFIG_MAP_NAME = 'cray-product-catalog'
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE = 'services'
    COMPONENT_VERSIONS_PRODUCT_MAP_KEY = 'component_versions'

    def __init__(self, name, version):
        self.name = name
        self.version = version
        self._docker_image_name = None

    @property
    def group_repo_name(self):
        """Get the name of this product's 'group' repository, i.e. NAME-DIST"""
        return f'{self.name}-{self.DIST}'

    @property
    def hosted_repo_name(self):
        """Get the name of the hosted repository, i.e. NAME-VERSION-DIST"""
        return f'{self.name}-{self.version}-{self.DIST}'

    @cached_property
    def docker_image_version(self):
        """Get the name of the docker image associated with this version.

        Returns:
            str: The name of the docker image.
        """
        # This makes some assumptions about the product:
        # * The product has exactly one docker image
        # * The image's version can be found in the product catalog under "component_versions"
        # Load k8s configuration before trying to use API
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=YAMLLoadWarning)
                load_kube_config()
            config_map = CoreV1Api().read_namespaced_config_map(
                name=self.PRODUCT_CATALOG_CONFIG_MAP_NAME,
                namespace=self.PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
            )
        except ConfigException as err:
            print('Unable to load kubernetes configuration: %s.', err)
            return None
        except MaxRetryError as err:
            print('Unable to connect to Kubernetes to read cray-product-catalog configuration map: %s.', err)
            return None
        except ApiException as err:
            # The full string representation of ApiException is very long, so just log err.reason.
            print('Error reading cray-product-catalog configuration map: %s.', err.reason)
            return None

        product_config_map_entry = config_map.data.get(self.name)
        if product_config_map_entry is None:
            print(f'{self.name} is not in the {self.PRODUCT_CATALOG_CONFIG_MAP_NAME} config map.')
            return None
        product_config_map_entry = safe_load(product_config_map_entry)
        if self.version not in product_config_map_entry:
            print(f'{self.name}-{self.version} is not in the {self.PRODUCT_CATALOG_CONFIG_MAP_NAME} config map.')
            return None
        product_version_config_map_entry = product_config_map_entry[self.version]
        if self.COMPONENT_VERSIONS_PRODUCT_MAP_KEY not in product_version_config_map_entry:
            print(f'{self.name}-{self.version} entry in {self.PRODUCT_CATALOG_CONFIG_MAP_NAME} '
                  f'does not contain "{self.COMPONENT_VERSIONS_PRODUCT_MAP_KEY}".')
            return None
        product_version_component_versions = product_version_config_map_entry[self.COMPONENT_VERSIONS_PRODUCT_MAP_KEY]
        if self.name not in product_version_component_versions:
            print(f'{self.name}-{self.version} does not contain expected "{self.COMPONENT_VERSIONS_PRODUCT_MAP_KEY}".')
            return None

        return product_version_component_versions[self.name]

    def uninstall(self, nexus_api, docker_api):
        """Uninstall a version by removing its package repository from Nexus.

        Args:
            nexus_api (ExtendedNexusAPI): The API to interface with Nexus.
            docker_api (ExtendedDockerAPI): The API to interface with the Nexus Docker registry.

        Returns:
            None
        """
        # TODO: raises exceptions from NexusApi
        try:
            nexus_api.repos.delete(self.hosted_repo_name)
        except NexusCtlHttpError as err:
            # TODO: we should be able to reduce some duplicated code in the error handling here.
            if err.code == 404:
                print(f'{self.hosted_repo_name} has already been removed from {self.group_repo_name} repository.')
            else:
                raise
        else:
            print(f'Repository {self.hosted_repo_name} has been removed.')
        # TODO: This doesn't check whether any other currently-installed products depend on this image.
        # This makes the assumption that the product's image is named cray/cray-{product}
        if self.docker_image_version is not None:
            try:
                docker_api.delete_image_with_missing_layers(f'cray/cray-{self.name}', self.docker_image_version)
            except NexusCtlHttpError as err:
                if err.code == 404:
                    print(f'Image cray/cray-{self.name}:{self.docker_image_version} has already been removed.')
                else:
                    raise
            else:
                print(f'Image cray/cray-{self.name}:{self.docker_image_version} has been removed.')
        else:
            print(f'No docker image found for {self.name}-{self.version}.')

    def activate(self, nexus_api):
        """Activate a version.

        This uses the Nexus API to make a hosted-type repo the first entry in a
        group-type repo.

        Args:
            nexus_api (ExtendedNexusAPI): The API to interface with Nexus.

        Returns:
            None

        Raises:
            NexusAPIError: if the group repo is not found or multiple
                exist with the same name.
        """
        nexus_api.activate_group_repo_member(self.group_repo_name, self.hosted_repo_name)
        print(f'Repository {self.hosted_repo_name} is now the default in {self.group_repo_name}.')
