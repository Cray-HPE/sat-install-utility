"""
Unit tests for the sat_install_utility.main module.

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

import unittest
from unittest.mock import Mock, patch

from kubernetes.config import ConfigException


from sat_install_utility.main import (
    activate,
    get_k8s_api,
    main,
    uninstall,
    PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
    PRODUCT_CATALOG_CONFIG_MAP_NAME
)
from sat_install_utility.products import ProductInstallException


class TestGetK8sAPI(unittest.TestCase):
    """Tests for get_k8s_api()."""

    def setUp(self):
        """Set up mocks."""
        self.mock_load_kube_config = patch('sat_install_utility.main.load_kube_config').start()
        self.mock_corev1api = patch('sat_install_utility.main.CoreV1Api').start()

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_get_k8s_api(self):
        """Test the successful case of get_k8s_api."""
        api = get_k8s_api()
        self.mock_load_kube_config.assert_called_once_with()
        self.mock_corev1api.assert_called_once_with()
        self.assertEqual(api, self.mock_corev1api.return_value)

    def test_get_k8s_api_config_exception(self):
        """Test when configuration can't be loaded."""
        self.mock_load_kube_config.side_effect = ConfigException
        with self.assertRaises(SystemExit):
            get_k8s_api()
        self.mock_load_kube_config.assert_called_once_with()
        self.mock_corev1api.assert_not_called()


class TestActivateUninstall(unittest.TestCase):
    """Tests for activate() and uninstall()."""
    def setUp(self):
        self.mock_product_catalog_cls = patch('sat_install_utility.main.ProductCatalog').start()
        self.mock_product_catalog = self.mock_product_catalog_cls.return_value
        self.mock_docker = Mock()
        self.mock_nexus = Mock()
        self.mock_k8s_api = patch('sat_install_utility.main.get_k8s_api').start().return_value

    def test_activate_success(self):
        """Test the successful case for activate()."""
        activate('mock_name', 'mock_version', 'mock_dist', self.mock_nexus)
        self.mock_product_catalog_cls.assert_called_once_with(
            PRODUCT_CATALOG_CONFIG_MAP_NAME,
            PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
            self.mock_k8s_api
        )
        self.mock_product_catalog.get_product.assert_called_once_with(
            'mock_name', 'mock_version'
        )
        mock_product = self.mock_product_catalog.get_product.return_value
        mock_product.activate_hosted_repo.assert_called_once_with(self.mock_nexus, 'mock_dist')

    def test_uninstall_success(self):
        """Test the successful case for uninstall()."""
        uninstall('mock_name', 'mock_version', 'mock_dist', self.mock_nexus, self.mock_docker)
        self.mock_product_catalog_cls.assert_called_once_with(
            PRODUCT_CATALOG_CONFIG_MAP_NAME,
            PRODUCT_CATALOG_CONFIG_MAP_NAMESPACE,
            self.mock_k8s_api
        )
        self.mock_product_catalog.remove_product_docker_images.assert_called_once_with(
            'mock_name', 'mock_version', self.mock_docker
        )
        self.mock_product_catalog.get_product.assert_called_once_with(
            'mock_name', 'mock_version'
        )
        mock_product = self.mock_product_catalog.get_product.return_value
        mock_product.uninstall_hosted_repo.assert_called_once_with(self.mock_nexus, 'mock_dist')


class TestMain(unittest.TestCase):
    def setUp(self):
        """Set up mocks."""
        self.mock_nexus_client_cls = patch('sat_install_utility.main.NexusClient').start()
        self.mock_docker_client_cls = patch('sat_install_utility.main.DockerClient').start()
        self.mock_nexus_api_cls = patch('sat_install_utility.main.NexusApi').start()
        self.mock_docker_api_cls = patch('sat_install_utility.main.DockerApi').start()
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
            'sat',
            '2.0.3',
            'sle-15sp2',
            self.mock_nexus_api_cls.return_value
        )

    def test_uninstall_action(self):
        """Test a basic uninstall."""
        patch('sys.argv', ['sat-install-utility', 'uninstall', '2.0.3']).start()
        main()
        self.mock_uninstall.assert_called_once_with(
            'sat',
            '2.0.3',
            'sle-15sp2',
            self.mock_nexus_api_cls.return_value,
            self.mock_docker_api_cls.return_value
        )

    def test_activate_with_error(self):
        """Test activate when a ProductInstallException occurs."""
        patch('sys.argv', ['sat-install-utility', 'activate', '2.0.3']).start()
        self.mock_activate.side_effect = ProductInstallException('Failed')
        with self.assertRaises(SystemExit):
            main()

    def test_override_docker_and_nexus_urls(self):
        """Test with overridden Docker and Nexus API URLs."""
        mock_argv = [
            'sat-install-utility', 'uninstall', '2.0.3',
            '--docker-url=my-registry.com', '--nexus-url=my-nexus.biz'
        ]
        patch('sys.argv', mock_argv).start()
        main()
        self.mock_nexus_client_cls.assert_called_once_with('my-nexus.biz')
        self.mock_docker_client_cls.assert_called_once_with('my-registry.com')
        self.mock_nexus_api_cls.assert_called_once_with(self.mock_nexus_client_cls.return_value)
        self.mock_docker_api_cls.assert_called_once_with(self.mock_docker_client_cls.return_value)
        self.mock_uninstall.assert_called_once_with(
            'sat',
            '2.0.3',
            'sle-15sp2',
            self.mock_nexus_api_cls.return_value,
            self.mock_docker_api_cls.return_value
        )

    def test_uninstall_with_dist(self):
        """Test with overridden distribution value."""
        mock_argv = [
            'sat-install-utility', 'uninstall', '2.0.3', '--dist=sle-15sp3'
        ]
        patch('sys.argv', mock_argv).start()
        main()
        self.mock_uninstall.assert_called_once_with(
            'sat',
            '2.0.3',
            'sle-15sp3',
            self.mock_nexus_api_cls.return_value,
            self.mock_docker_api_cls.return_value
        )


if __name__ == '__main__':
    unittest.main()
