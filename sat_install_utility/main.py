"""
Entry point for the SAT install utility.

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

import argparse
import warnings

from kubernetes.config import load_kube_config, ConfigException
from kubernetes.client import CoreV1Api
from nexusctl import DockerApi, DockerClient, NexusApi, NexusClient
from nexusctl.common import DEFAULT_DOCKER_REGISTRY_API_BASE_URL, DEFAULT_NEXUS_API_BASE_URL
from yaml import YAMLLoadWarning

from sat_install_utility.products import ProductCatalog, ProductInstallException

PRODUCT_CATALOG_CONFIG_MAP_NAME = 'cray-product-catalog'
PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE = 'services'


def get_k8s_api():
    """Load a Kubernetes CoreV1Api and return it.

    Returns:
        CoreV1Api: The Kubernetes API.

    Raises:
        SystemExit: if there was an error loading the Kubernetes configuration.
    """
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=YAMLLoadWarning)
            load_kube_config()
        return CoreV1Api()
    except ConfigException as err:
        print(f'Unable to load kubernetes configuration: {err}.')
        raise SystemExit(1)


def create_parser():
    """Create an argument parser for this command.

    Returns:
        argparse.ArgumentParser: The parser.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'action',
        choices=['uninstall', 'activate'],
        help='Specify the operation to execute on a product.'
    )
    parser.add_argument(
        'product',
        choices=['sat'],
        help='Specify the name of the product to operate on.'
    )
    parser.add_argument(
        'version',
        help='Specify the version of the product to operate on.'
    )
    parser.add_argument(
        '--dist',
        default='sle-15sp2',
        help='When manipulating group and hosted repositories, specify the '
             'name of the distribution, which is assumed to be the tail of the'
             'repositories\' names, e.g. sat-2.11-sle-15sp2.'
    )
    parser.add_argument(
        '--nexus-url',
        default=DEFAULT_NEXUS_API_BASE_URL,
        help='Specify the base URL of Nexus.'
    )
    parser.add_argument(
        '--docker-url',
        default=DEFAULT_DOCKER_REGISTRY_API_BASE_URL,
        help='Specify the base URL of the Docker registry.'
    )

    return parser


def uninstall(name, version, dist, nexus_api, docker_api):
    """Uninstall a version of a product.

    Args:
        name (str): The name of the product, e.g. 'sat'
        version (str): The version of the product, e.g. '2.1.11'
        dist (str): Specify the distribution for the hosted repository to remove.
        nexus_api (NexusApi): The nexusctl Nexus API to interface with
            Nexus.
        docker_api (DockerApi): The nexusctl Docker API to interface with
            the Docker registry.

    Returns:
        None

    Raises:
        ProductInstallException: if uninstall failed.
    """
    product_catalog = ProductCatalog(
        PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, get_k8s_api()
    )
    product_to_uninstall, other_products = product_catalog.get_matching_products(name, version)

    product_to_uninstall.uninstall_hosted_repo(nexus_api, dist)

    # TODO(CRAYSAT-1033): Will have to be modified slightly for multiple Docker images per product
    other_products_with_same_docker_image = [
        product for product in other_products
        if product.docker_image_name == product_to_uninstall.docker_image_name
        and product.docker_image_version == product_to_uninstall.docker_image_version
    ]
    if other_products_with_same_docker_image:
        print(f'Not removing Docker image '
              f'{product_to_uninstall.docker_image_name}:{product_to_uninstall.docker_image_version} '
              f'used by the following other product versions: '
              f'{", ".join(str(p) for p in other_products_with_same_docker_image)}')
    else:
        product_to_uninstall.uninstall_docker_image(docker_api)

    product_to_uninstall.remove_from_product_catalog(
        PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
    )


def activate(name, version, dist, nexus_api):
    """Activate a version of a product.

    Args:
        name (str): The name of the product, e.g. 'sat'
        version (str): The version of the product, e.g. '2.1.11'
        dist (str): The name of the distribution associated with the hosted
            and group repositories.
        nexus_api (NexusApi): The nexusctl Nexus API to interface with
            Nexus.

    Returns:
        None

    Raises:
        ProductInstallException: If activation failed.
    """
    product_catalog = ProductCatalog(
        PRODUCT_CATALOG_CONFIG_MAP_NAME, PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE, get_k8s_api()
    )
    product_to_activate = product_catalog.get_matching_products(name, version)[0]
    product_to_activate.activate_hosted_repo(nexus_api, dist)


def main():
    """Main entry point.

    Returns:
        None

    Raises:
        SystemExit: if a ProductInstallException occurs.
    """
    parser = create_parser()
    args = parser.parse_args()
    try:
        if args.action == 'uninstall':
            uninstall(
                args.product, args.version, args.dist, NexusApi(NexusClient(args.nexus_url)),
                DockerApi(DockerClient(args.docker_url))
            )
        elif args.action == 'activate':
            activate(
                args.product, args.version, args.dist, NexusApi(NexusClient(args.nexus_url))
            )
    except ProductInstallException as err:
        print(err)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
