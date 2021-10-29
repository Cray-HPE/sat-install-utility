"""
Unit tests for the sat_install_utility.main module.

(C) Copyright 2021 Hewlett Packard Enterprise Development LP.
"""

from argparse import Namespace
import unittest
from unittest.mock import patch


from sat_install_utility.main import (
    activate,
    main,
    uninstall,
    PRODUCT
)
from shasta_install_utility_common.products import ProductInstallException
from shasta_install_utility_common.constants import (
    DEFAULT_DOCKER_URL,
    DEFAULT_NEXUS_URL,
    PRODUCT_CATALOG_CONFIG_MAP_NAME,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE
)


class TestActivateUninstall(unittest.TestCase):
    """Tests for activate() and uninstall()."""
    def setUp(self):
        self.mock_product_catalog_cls = patch('sat_install_utility.main.ProductCatalog').start()
        self.mock_product_catalog = self.mock_product_catalog_cls.return_value

    def test_activate_success(self):
        """Test the successful case for activate()."""
        activate(Namespace(
            version='mock_version',
            docker_url='mock_docker_url',
            nexus_url='mock_nexus_url',
            product_catalog_name='mock_name',
            product_catalog_namespace='mock_namespace'
        ))
        self.mock_product_catalog_cls.assert_called_once_with(
            name='mock_name',
            namespace='mock_namespace',
            docker_url='mock_docker_url',
            nexus_url='mock_nexus_url',
        )
        self.mock_product_catalog.activate_product_hosted_repos.assert_called_once_with(PRODUCT, 'mock_version')

    def test_uninstall_success(self):
        """Test the successful case for uninstall()."""
        uninstall(Namespace(
            version='mock_version',
            docker_url='mock_docker_url',
            nexus_url='mock_nexus_url',
            product_catalog_name='mock_name',
            product_catalog_namespace='mock_namespace'
        ))
        self.mock_product_catalog_cls.assert_called_once_with(
            name='mock_name',
            namespace='mock_namespace',
            docker_url='mock_docker_url',
            nexus_url='mock_nexus_url',
        )
        self.mock_product_catalog.remove_product_docker_images.assert_called_once_with(PRODUCT, 'mock_version')
        self.mock_product_catalog.uninstall_product_hosted_repos.assert_called_once_with(PRODUCT, 'mock_version')
        self.mock_product_catalog.remove_product_entry.assert_called_once_with(PRODUCT, 'mock_version')


class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up mocks."""
        self.mock_activate = patch('sat_install_utility.main.activate').start()
        self.mock_uninstall = patch('sat_install_utility.main.uninstall').start()

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_activate_action(self):
        """Test a basic activate."""
        patch('sys.argv', ['sat-install-utility', 'activate', '2.0.3']).start()
        main()
        self.mock_activate.assert_called_once_with(
            Namespace(
                action='activate',
                docker_url=DEFAULT_DOCKER_URL,
                nexus_url=DEFAULT_NEXUS_URL,
                product_catalog_name=PRODUCT_CATALOG_CONFIG_MAP_NAME,
                product_catalog_namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                version='2.0.3'
            )
        )

    def test_uninstall_action(self):
        """Test a basic uninstall."""
        patch('sys.argv', ['sat-install-utility', 'uninstall', '2.0.3']).start()
        main()
        self.mock_uninstall.assert_called_once_with(
            Namespace(
                action='uninstall',
                docker_url=DEFAULT_DOCKER_URL,
                nexus_url=DEFAULT_NEXUS_URL,
                product_catalog_name=PRODUCT_CATALOG_CONFIG_MAP_NAME,
                product_catalog_namespace=PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
                version='2.0.3'
            )
        )

    def test_activate_with_error(self):
        """Test activate when a ProductInstallException occurs."""
        patch('sys.argv', ['sat-install-utility', 'activate', '2.0.3']).start()
        self.mock_activate.side_effect = ProductInstallException('Failed')
        with self.assertRaises(SystemExit) as err_cm:
            main()
        self.assertEqual(err_cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
