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
    uninstall
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
        """Set up mocks."""
        self.mock_get_k8s_api = patch('sat_install_utility.main.get_k8s_api').start()
        self.mock_product_catalog_cls = patch('sat_install_utility.main.ProductCatalog').start()
        self.mock_product_catalog = self.mock_product_catalog_cls.return_value
        self.fake_products = [
            # Multiple versions of SAT that have some images in common with one another.
            Mock(product_name='sat', version='2.0.3', docker_images={'cray/cray-sat': '3.4.0',
                                                                     'cray/sat-cfs-install': '1.2.3'}),
            Mock(product_name='sat', version='2.0.4', docker_images={'cray/cray-sat': '3.5.0'}),
            Mock(product_name='sat', version='2.2.5', docker_images={'cray/cray-sat': '3.5.0',
                                                                     'cray/sat-cfs-install': '1.2.3',
                                                                     'cray/sat-install-utility': '1.1.0'}),
            # Two versions of COS with different images, but same image version numbers as the SAT products above.
            Mock(product_name='cos', version='2.0.5', docker_images={'cray/cray-cos': '3.4.0'}),
            Mock(product_name='cos', version='2.0.6', docker_images={'cray/cray-cos': '3.5.0'}),
            # Two products that each have a single docker image, and are the same image.
            Mock(product_name='sat', version='2.0.1', docker_images={'cray/cray-sat': '3.1.0'}),
            Mock(product_name='another-product', version='1.2.3', docker_images={'cray/cray-sat': '3.1.0'})
        ]
        [p.configure_mock(name=p.product_name) for p in self.fake_products]

        self.mock_product_catalog.products = self.fake_products
        self.mock_product_catalog.get_matching_products.side_effect = self.mock_get_matching_products
        self.mock_print = patch('builtins.print').start()
        self.mock_nexus_api = Mock()
        self.mock_docker_api = Mock()

    def mock_get_matching_products(self, name, version):
        """Mock the behavior of ProductCatalog.get_matching_products()."""
        matching = [p for p in self.mock_product_catalog.products if p.name == name and p.version == version][0]
        others = [p for p in self.mock_product_catalog.products if p.name != name or p.version != version]
        return matching, others

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_uninstall_success(self):
        """Test a successful uninstall."""
        uninstall(
            name='sat',
            version='2.0.3',
            dist='sle-15sp3',
            nexus_api=self.mock_nexus_api,
            docker_api=self.mock_docker_api,
        )
        product = self.fake_products[0]
        product.uninstall_hosted_repo.assert_called_once_with(self.mock_nexus_api, 'sle-15sp3')
        product.uninstall_docker_image.assert_called_once_with('cray/cray-sat', '3.4.0', self.mock_docker_api)
        product.remove_from_product_catalog.assert_called_once_with('cray-product-catalog', 'services')

    def test_uninstall_without_docker_image_removal(self):
        """Test a successful uninstall when a Docker image is not removed."""
        uninstall(
            name='sat',
            version='2.0.1',
            dist='sle-15sp3',
            nexus_api=self.mock_nexus_api,
            docker_api=self.mock_docker_api,
        )
        product = self.fake_products[-2]
        product.uninstall_hosted_repo.assert_called_once_with(self.mock_nexus_api, 'sle-15sp3')
        product.uninstall_docker_image.assert_not_called()
        expected_print_output = (
            f'Not removing Docker image cray/cray-sat:3.1.0 '
            f'used by the following other product versions: {str(self.fake_products[-1])}'
        )
        self.mock_print.assert_called_with(expected_print_output)
        product.remove_from_product_catalog.assert_called_once_with('cray-product-catalog', 'services')

    def test_uninstall_with_partial_docker_image_removal(self):
        """Test uninstalling a version where one of the Docker images is shared."""
        uninstall(
            name='sat',
            version='2.2.5',
            dist='sle-15sp3',
            nexus_api=self.mock_nexus_api,
            docker_api=self.mock_docker_api,
        )
        product = self.fake_products[2]
        product.uninstall_hosted_repo.assert_called_once_with(self.mock_nexus_api, 'sle-15sp3')
        expected_print_output = [
            (
                f'Not removing Docker image cray/cray-sat:3.5.0 '
                f'used by the following other product versions: {str(self.fake_products[1])}'
            ),
            (
                f'Not removing Docker image cray/sat-cfs-install:1.2.3 '
                f'used by the following other product versions: {str(self.fake_products[0])}'
            )
        ]
        for output in expected_print_output:
            self.mock_print.assert_any_call(output)
        product.uninstall_docker_image.assert_called_once_with(
            'cray/sat-install-utility', '1.1.0', self.mock_docker_api
        )
        product.remove_from_product_catalog.assert_called_once_with('cray-product-catalog', 'services')

    def test_activate_success(self):
        """Test a successful activation."""
        activate(
            name='sat',
            version='2.0.3',
            dist='sle-15sp3',
            nexus_api=self.mock_nexus_api
        )
        product = self.fake_products[0]
        product.activate_hosted_repo.assert_called_once_with(self.mock_nexus_api, 'sle-15sp3')


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
        patch('sys.argv', ['sat-install-utility', 'activate', 'sat', '2.0.3']).start()
        main()
        self.mock_activate.assert_called_once_with(
            'sat',
            '2.0.3',
            'sle-15sp2',
            self.mock_nexus_api_cls.return_value
        )

    def test_uninstall_action(self):
        """Test a basic uninstall."""
        patch('sys.argv', ['sat-install-utility', 'uninstall', 'sat', '2.0.3']).start()
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
        patch('sys.argv', ['sat-install-utility', 'activate', 'sat', '2.0.3']).start()
        self.mock_activate.side_effect = ProductInstallException('Failed')
        with self.assertRaises(SystemExit):
            main()

    def test_override_docker_and_nexus_urls(self):
        """Test with overridden Docker and Nexus API URLs."""
        mock_argv = [
            'sat-install-utility', 'uninstall', 'sat', '2.0.3',
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
            'sat-install-utility', 'uninstall', 'sat', '2.0.3', '--dist=sle-15sp3'
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
