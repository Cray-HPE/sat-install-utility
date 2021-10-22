"""
Entry point for the SAT install utility.

(C) Copyright 2021 Hewlett Packard Enterprise Development LP.
"""


from shasta_install_utility_common.products import ProductCatalog, ProductInstallException
from shasta_install_utility_common.parser import create_parser

PRODUCT = 'sat'


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
