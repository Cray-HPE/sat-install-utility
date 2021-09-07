"""
Unit tests for the sat_install_utility.products module.

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

from subprocess import CalledProcessError
import unittest
from unittest.mock import Mock, patch

from yaml import safe_dump

from sat_install_utility.products import (
    ProductCatalog,
    ProductInstallException,
    InstalledProductVersion
)


class TestProductCatalog(unittest.TestCase):
    """Tests for the ProductCatalog class."""
    def setUp(self):
        """Set up mocks."""
        self.mock_k8s_api = Mock()
        self.mock_product_catalog_data = {
            'sat': safe_dump({
                '2.0.0': {'component_versions': {'sat': '1.0.0', 'sat-subpackage': '1.4.0'}},
                '2.0.1': {'component_versions': {'sat': '1.0.1', 'sat-subpackage': '1.4.0'}},
                '2.0.2': {'component_versions': {'sat': '1.0.1', 'sat-subpackage': '1.4.1'}},
            }),
            'cos': safe_dump({
                '2.0.0': {'component_versions': {'cos': '1.0.0', 'cos-subpackage': '1.4.0'}},
                '2.0.1': {'component_versions': {'cos': '1.0.1', 'cos-subpackage': '1.4.0'}},
                '2.0.2': {'component_versions': {'cos': '1.0.1', 'cos-subpackage': '1.4.1'}},
            })
        }
        self.mock_k8s_api.read_namespaced_config_map.return_value = Mock(data=self.mock_product_catalog_data)

    def create_and_assert_product_catalog(self):
        """Assert the product catalog was created as expected."""
        product_catalog = ProductCatalog('mock-name', 'mock-namespace', self.mock_k8s_api)
        self.mock_k8s_api.read_namespaced_config_map.assert_called_once_with('mock-name', 'mock-namespace')
        return product_catalog

    def test_create_product_catalog(self):
        """Test creating a simple ProductCatalog."""
        product_catalog = self.create_and_assert_product_catalog()
        expected_names_and_versions = [
            (name, version) for name in ('sat', 'cos') for version in ('2.0.0', '2.0.1', '2.0.2')
        ]
        actual_names_and_versions = [
            (product.name, product.version) for product in product_catalog.products
        ]
        self.assertEqual(expected_names_and_versions, actual_names_and_versions)

    def test_create_product_catalog_invalid_product_data(self):
        """Test creating a ProductCatalog when the product catalog contains invalid data."""
        self.mock_product_catalog_data['sat'] = '\t'
        with self.assertRaisesRegex(ProductInstallException, 'Failed to load ConfigMap data'):
            self.create_and_assert_product_catalog()

    def test_create_product_catalog_null_data(self):
        """Test creating a ProductCatalog when the product catalog contains null data."""
        self.mock_k8s_api.read_namespaced_config_map.return_value = Mock(data=None)
        with self.assertRaisesRegex(ProductInstallException,
                                    'No data found in mock-namespace/mock-name ConfigMap.'):
            self.create_and_assert_product_catalog()

    def test_get_matching_products(self):
        """Test getting a particular product by name/version."""
        product_catalog = self.create_and_assert_product_catalog()
        expected_matching_name_and_version = ('cos', '2.0.0')
        expected_other_versions = [('sat', version) for version in ('2.0.0', '2.0.1', '2.0.2')]
        expected_other_versions.extend([('cos', version) for version in ('2.0.1', '2.0.2')])
        actual_matching_product, actual_other_versions = product_catalog.get_matching_products('cos', '2.0.0')
        self.assertEqual(
            expected_matching_name_and_version, (actual_matching_product.name, actual_matching_product.version)
        )
        self.assertEqual(
            [(name, version) for name, version in expected_other_versions],
            [(product.name, product.version) for product in actual_other_versions]
        )
        expected_component_data = {'component_versions': {'cos': '1.0.0', 'cos-subpackage': '1.4.0'}}
        self.assertEqual(expected_component_data, actual_matching_product.data)


class TestInstalledProductVersion(unittest.TestCase):
    def setUp(self):
        """Set up mocks."""
        self.installed_product_version = InstalledProductVersion(
            'sat',
            '2.2.0',
            {
                'component_versions': {
                    'docker': {
                        'cray/cray-sat': '3.9.0',
                        'cray/sat-cfs-install': '1.2.0',
                        'cray/sat-install-utility': '3.9.0',
                    },
                    'rpm': {
                        'cray-sat-podman': '1.5.0'
                    }
                }
            }
        )
        self.legacy_installed_product_version = InstalledProductVersion(
            'sat', '1.0.1', {'component_versions': {'sat': '1.0.0'}}
        )

        self.mock_nexus_api = Mock()
        self.mock_group_members = ['sat-3.0.0-sle-15sp3', 'sat-2.2.0-sle-15sp3', 'sat-1.0.1-sle-15sp3']
        self.mock_group_repo = Mock()
        self.mock_group_repo.group.member_names = self.mock_group_members
        # This is slightly incorrect as NexusApi.repos.list may also return a
        # hosted repo, but good enough for the test.
        self.mock_nexus_api.repos.list.return_value = [self.mock_group_repo]
        self.mock_docker_api = Mock()
        self.mock_environ = patch('sat_install_utility.products.os.environ').start()
        self.mock_check_output = patch('sat_install_utility.products.subprocess.check_output').start()

    def tearDown(self):
        """Stop patches."""
        patch.stopall()

    def test_docker_images(self):
        """Test getting the Docker images."""
        expected_docker_image_versions = {'cray/cray-sat': '3.9.0',
                                          'cray/sat-cfs-install': '1.2.0',
                                          'cray/sat-install-utility': '3.9.0'}
        self.assertEqual(
            expected_docker_image_versions, self.installed_product_version.docker_images
        )

    def test_legacy_docker_images(self):
        """Test getting the Docker images from an 'old'-style product catalog entry."""
        expected_docker_image_versions = {'cray/cray-sat': '1.0.0'}
        self.assertEqual(
            expected_docker_image_versions, self.legacy_installed_product_version.docker_images
        )

    def test_no_docker_images(self):
        """Test a product that has an empty dictionary under the 'docker' key returns an empty dictionary."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': {}}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, {})

    def test_no_docker_images_null(self):
        """Test a product that has None under the 'docker' key returns an empty dictionary."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': None}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, {})

    def test_no_docker_images_empty_list(self):
        """Test a product that has an empty list under the 'docker' key returns an empty dictionary."""
        product_with_no_docker_images = InstalledProductVersion(
            'sat', '0.9.9', {'component_versions': {'docker': []}}
        )
        self.assertEqual(product_with_no_docker_images.docker_images, {})

    def test_str(self):
        """Test the string representation of InstalledProductVersion."""
        expected_str = 'sat-2.2.0'
        self.assertEqual(
            expected_str, str(self.installed_product_version)
        )

    def test_get_group_repo_name(self):
        """Test getting a group repo name for an InstalledProductVersion."""
        expected_group_repo_name = 'sat-sle-15sp3'
        self.assertEqual(
            expected_group_repo_name, self.installed_product_version.get_group_repo_name('sle-15sp3')
        )

    def test_get_hosted_repo_name(self):
        """Test getting a hosted repo name for an InstalledProductVersion."""
        expected_hosted_repo_name = 'sat-2.2.0-sle-15sp3'
        self.assertEqual(
            expected_hosted_repo_name, self.installed_product_version.get_hosted_repo_name('sle-15sp3')
        )

    def test_uninstall_hosted_repo(self):
        """Test uninstalling a hosted repo for an InstalledProductVersion."""
        self.installed_product_version.uninstall_hosted_repo(self.mock_nexus_api, 'sle-15sp3')
        self.mock_nexus_api.repos.delete.assert_called_once_with('sat-2.2.0-sle-15sp3')

    def test_uninstall_docker_image(self):
        """Test uninstalling a Docker image for an InstalledProductVersion."""
        self.installed_product_version.uninstall_docker_image('foo', 'bar', self.mock_docker_api)
        self.mock_docker_api.delete_image.assert_called_once_with('foo', 'bar')

    def test_activate_hosted_repo(self):
        """Test activating a product version's hosted repository."""
        self.installed_product_version.activate_hosted_repo(self.mock_nexus_api, 'sle-15sp3')
        self.mock_nexus_api.repos.raw_group.update.assert_called_once_with(
            self.mock_group_repo.name,
            self.mock_group_repo.online,
            self.mock_group_repo.storage.blobstore_name,
            self.mock_group_repo.storage.strict_content_type_validation,
            member_names=('sat-2.2.0-sle-15sp3',)
        )

    def test_remove_from_product_catalog(self):
        """Test removing a version from the product catalog."""
        self.installed_product_version.remove_from_product_catalog('mock-name', 'mock-namespace')
        self.mock_environ.update.assert_called_once_with({
            'PRODUCT': self.installed_product_version.name,
            'PRODUCT_VERSION': self.installed_product_version.version,
            'CONFIG_MAP': 'mock-name',
            'CONFIG_MAP_NS': 'mock-namespace'
        })
        self.mock_check_output.assert_called_once_with(['catalog_delete.py'])

    def test_remove_from_product_catalog_fail(self):
        """Test removing a version from the product catalog when the subcommand fails."""
        expected_err_regex = (
            f'Error removing {self.installed_product_version.name}-'
            f'{self.installed_product_version.version} from product catalog'
        )
        self.mock_check_output.side_effect = CalledProcessError(1, 'catalog_delete.py')
        with self.assertRaisesRegex(ProductInstallException, expected_err_regex):
            self.installed_product_version.remove_from_product_catalog('mock-name', 'mock-namespace')


if __name__ == '__main__':
    unittest.main()
