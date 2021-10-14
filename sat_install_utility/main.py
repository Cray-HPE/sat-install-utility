"""
Entry point for the SAT install utility.

(C) Copyright 2021 Hewlett Packard Enterprise Development LP.
"""

import argparse

from shasta_install_utility_common.constants import (
    DEFAULT_DOCKER_URL,
    DEFAULT_NEXUS_URL,
    PRODUCT_CATALOG_CONFIG_MAP_NAME,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
)
from shasta_install_utility_common.products import ProductCatalog, ProductInstallException

PRODUCT = 'sat'


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
        'version',
        help='Specify the version of the product to operate on.'
    )
    parser.add_argument(
        '--nexus-url',
        help='Override the base URL of Nexus.',
        default=DEFAULT_NEXUS_URL
    )
    parser.add_argument(
        '--docker-url',
        help='Override the base URL of the Docker registry.',
        default=DEFAULT_DOCKER_URL,
    )
    parser.add_argument(
        '--product-catalog-name',
        help='The name of the product catalog Kubernetes ConfigMap',
        default=PRODUCT_CATALOG_CONFIG_MAP_NAME
    )
    parser.add_argument(
        '--product-catalog-namespace',
        help='The namespace of the product catalog Kubernetes ConfigMap',
        default=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
    )

    return parser


def uninstall(args):
    """Uninstall a version of a product.

    Args:
        args (argparse.Namespace): The CLI arguments to the command.

    Returns:
        None

    Raises:
        ProductInstallException: if uninstall failed.
    """
    product_catalog = ProductCatalog(
        name=args.product_catalog_name,
        namespace=args.product_catalog_namespace,
        nexus_url=args.nexus_url,
        docker_url=args.docker_url
    )
    product_catalog.remove_product_docker_images(PRODUCT, args.version)
    product_catalog.uninstall_product_hosted_repos(PRODUCT, args.version)
    product_catalog.remove_product_entry(PRODUCT, args.version)


def activate(args):
    """Activate a version of a product.

    Args:
        args (argparse.Namespace): The CLI arguments to the command.

    Returns:
        None

    Raises:
        ProductInstallException: If activation failed.
    """
    product_catalog = ProductCatalog(
        name=args.product_catalog_name,
        namespace=args.product_catalog_namespace,
        nexus_url=args.nexus_url,
        docker_url=args.docker_url
    )
    product_catalog.activate_product_hosted_repos(PRODUCT, args.version)


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
            uninstall(args)
        elif args.action == 'activate':
            activate(args)
    except ProductInstallException as err:
        print(err)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
