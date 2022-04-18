"""
Entry point for the SAT install utility.

(C) Copyright 2021-2022 Hewlett Packard Enterprise Development LP.
"""

import logging

from cfs_config_util.activation import cfs_activate_version
from shasta_install_utility_common.products import ProductCatalog, ProductInstallException
from shasta_install_utility_common.parser import create_parser

from sat_install_utility.constants import (
    PRODUCT,
    PRODUCT_NCN_PLAYBOOK,
)


def configure_logging():
    """Configure logging for the root logger.

    This sets up the root logger with the default format, WARNING log level, and
    stderr log handler. This allows logging messages from cfs-config-util
    library code to be logged to stderr.

    Returns:
        None.
    """
    CONSOLE_LOG_FORMAT = '%(levelname)s: %(message)s'
    logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(CONSOLE_LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.WARNING)


def report_cfs_results(success_fail_tuple):
    """Helper function to report the results of a CFS update action.

    Args:
        success_fail_tuple ([str], [str]): tuple returned from
            cfs_activate_version

    Returns: None.

    Raises:
        ProductInstallException: if there are configurations that failed to
            update
    """
    succeeded, failed = success_fail_tuple
    if succeeded:
        print(f'Updated CFS configurations: [{", ".join(succeeded)}]')
    if failed:
        raise ProductInstallException(f'Could not update CFS configurations: '
                                      f'[{", ".join(failed)}]')


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
        docker_url=args.docker_url,
        nexus_credentials_secret_name=args.nexus_credentials_secret_name,
        nexus_credentials_secret_namespace=args.nexus_credentials_secret_namespace
    )
    product_catalog.remove_product_docker_images(PRODUCT, args.version)
    product_catalog.uninstall_product_hosted_repos(PRODUCT, args.version)
    product_catalog.remove_product_entry(PRODUCT, args.version)

    # TODO (CRAYSAT-1262): Remove CFS configuration layer as appropriate


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
        docker_url=args.docker_url,
        nexus_credentials_secret_name=args.nexus_credentials_secret_name,
        nexus_credentials_secret_namespace=args.nexus_credentials_secret_namespace
    )
    product_catalog.activate_product_hosted_repos(PRODUCT, args.version)
    product_catalog.activate_product_entry(PRODUCT, args.version)

    # TODO (CRAYSAT-1262): Abstract this into shasta-install-utility-common
    product_version = product_catalog.get_product(PRODUCT, args.version)
    if product_version.clone_url is None:
        print(f'CFS import for {PRODUCT} not detected; skipping CFS configuration.')
        return

    cfs_results = cfs_activate_version(
        PRODUCT,
        product_version.version,
        product_version.clone_url,
        PRODUCT_NCN_PLAYBOOK,
    )
    report_cfs_results(cfs_results)


def main():
    """Main entry point.

    Returns:
        None

    Raises:
        SystemExit: if a ProductInstallException occurs.
    """
    configure_logging()
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
