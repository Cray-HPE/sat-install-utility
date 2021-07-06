#!/usr/bin/env python
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

from sat_install_utility.nexus import ExtendedNexusAPI, ExtendedDockerAPI, NexusAPIError
from sat_install_utility.product_version import InstalledProductVersion


def create_parser():
    """Create an argument parser for this command.

    Returns:
        argparse.ArgumentParser: The parser.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['uninstall', 'activate'])
    parser.add_argument('product', choices=['sat'])
    parser.add_argument('version')

    return parser


def uninstall(product, version):
    """Uninstall a version of a product.

    Args:
        product: The name of the product, e.g. 'sat'
        version: The version of the product stream, e.g. '2.1.11'

    Returns:
        None
    """
    # TODO: override default nexus URL
    product_to_uninstall = InstalledProductVersion(product, version)
    product_to_uninstall.uninstall(ExtendedNexusAPI(), ExtendedDockerAPI())


def activate(product, version):
    """Activate a version of a product.

    Args:
        product: The name of the product, e.g. 'sat'
        version: The version of the product stream, e.g. '2.1.11'

    Returns:
        None
    """
    product_to_activate = InstalledProductVersion(product, version)
    try:
        # TODO: override default nexus URL
        product_to_activate.activate(ExtendedNexusAPI())
    except NexusAPIError as err:
        # TODO: handle exceptions from NexusApi (not just exceptions from ExtendedNexusAPI)
        # e.g. we get urllib.error.URLError from requests if SSL connection failed.
        # We should probably consolidate the error types and look at adding the extensions back into NexusApi
        print(err)
        raise SystemExit(1)


def main():
    """Main entry point.

    Returns:
        None
    """
    parser = create_parser()
    args = parser.parse_args()
    if args.action == 'uninstall':
        uninstall(args.product, args.version)
    elif args.action == 'activate':
        activate(args.product, args.version)


if __name__ == '__main__':
    main()
