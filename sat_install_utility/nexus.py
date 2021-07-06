"""
Contains some extensions to the NexusApi provided by nexusctl.

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

from nexusctl import DockerApi, NexusApi
from nexusctl.common.rest import NexusCtlHttpError


class NexusAPIError(Exception):
    """"""
    pass


class ExtendedNexusAPI(NexusApi):

    def get_repo_by_name(self, name):
        """Get a repository with the specified name.

        Args:
            name (str): The name of the repository.

        Returns:
            RepoListHostedEntry: If the repository is a hosted repository
            RepoListGroupEntry: If the repository is a group repository

        Raises:
            NexusAPIError: if more than one repository with the specified name
                is found, or if none are found with the specified name.
        """
        # TODO: raises exceptions from NexusApi too
        try:
            repos_matching_name = self.repos.list(regex=f'^{name}$')
            if len(repos_matching_name) > 1:
                raise NexusAPIError(f'More than one repository named {name} found.')
            return repos_matching_name[0]
        except IndexError:
            raise NexusAPIError(f'No repository named {name} found.')

    def activate_group_repo_member(self, group_repo_name, hosted_repo_name):
        """Add a hosted repository as the first member of a group repository.

        Args:
            group_repo_name (str): The name of a group repository.
            hosted_repo_name (str): The name of a hosted repository.

        Returns:
            None
        """
        # TODO: raises exceptions from NexusApi
        # Ensure hosted repo exists
        self.get_repo_by_name(hosted_repo_name)
        group_repo = self.get_repo_by_name(group_repo_name)
        # Put hosted repo first in the list, making it 'active'.
        members = [str(name) for name in group_repo.group.member_names if name != hosted_repo_name]
        members.insert(0, hosted_repo_name)

        self.repos.raw_group.update(
            group_repo.name,
            group_repo.online,
            group_repo.storage.blobstore_name,
            group_repo.storage.strict_content_type_validation,
            member_names=tuple(members)
        )


class ExtendedDockerAPI(DockerApi):

    def delete_image_with_missing_layers(self, name, tag):
        """Delete an image and handle when blobs might be missing

        Args:
            name (str): The name of the image to delete.
            tag (str): The tag of the image to delete.
        """
        hdr, _ = self.manifest.get(name, tag)
        self.manifest.delete(name, hdr.digest)
