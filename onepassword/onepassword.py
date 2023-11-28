import subprocess
import json

import onepassword.exceptions as opex

from packaging.version import Version
from typing import Dict, List


def get_op_cli_version() -> Version:
    """
    Retrieves the 1password-cli (op) version and returns the string version
    as a Version object.

    Returns:
        Version: a Version object with the current 1password-cli version information

    Raises:
        OnePasswordCLINotFound: If the 1password-CLI is not found due to a FileNotFoundError exception
    """
    cmd = ["op", "--version"]
    try:
        return Version(subprocess.run(cmd, capture_output=True, text=True).stdout)
    except FileNotFoundError:
        raise opex.OnePasswordCLINotFound(
            msg="Cannot find `op`, do you have 1password-cli installed?"
        )


def _run_cmd(cmd: List) -> subprocess.CompletedProcess | opex.OnePasswordRuntimeError:
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise opex.OnePasswordRuntimeError(
            f"Encountered an error when calling subprocess, got: {r.stderr}"
        )
    return r


def list_vaults() -> Dict | List[Dict]:
    """
    Return a list of all vaults accessible to the 1password account

    Returns:
         Dict | List[Dict]: either a single dictionary for a vault, or list of dictionaries for multiple vaults
    """

    cmd = ["op", "vault", "list", "--format", "json"]
    return json.loads(_run_cmd(cmd).stdout)


class OnePassword:
    """
    Entrypoint class for all 1Password related activities.
    There are no credentials to be passed to this class as it will use native integration with 1Password CLI
    https://developer.1password.com/docs/cli/get-started/
    """

    def __init__(self, vault: str = "Private") -> None:
        """
        Initialise the class with a vault, that by default is set to "Private".

        The class also grabs the 1Password CLI version and this is used as a catch to ensure that the CLI
        is installed before initialisation.

        Args:
             vault (str): string representation of which vault the class has to be initialised with.
                          Default is "Private"
        """
        self.op_cli_version = get_op_cli_version()
        self.vault = vault

    def get_item(self, item: str, fields: List = None) -> Dict | List[Dict]:
        """
        Returns either a string or dictionary response from 1Password

        Args:
            item (str): Can be either the name of the resource or its ID
            fields (list): (optional) This is to narrow down any field values for your return criteria.
                            e.g. receiving a list containing: ['username', 'password']
        Returns:
            Dict | List[Dict]: either a single item as a dictionary or multiple items as a list of dictionaries

        Raises:
            OnePasswordJSONError: if the response cannot be JSON loaded due to a JSONDecodeError exception
        """

        cmd = [
            "op",
            "item",
            "get",
            item,
            "--format",
            "json",
            "--vault",
            f"{self.vault}",
        ]

        if fields:
            _fields = []
            for field in fields:
                _fields.append(f"label={field}")
            cmd += ["--fields", ",".join(_fields)]

        r = _run_cmd(cmd)
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError as e:
            raise opex.OnePasswordJSONError(
                f"Cannot JSON load response from 1Password. Got {e}"
            )

    def get_value(self, item: str, field: str) -> str:
        """
        Retrieve an artefact from 1password and attempt to parse the field's value from it

        Args:
            item (str): name or UUID of item in Vault
            field (str): string of field name to use as label
        Returns:
            str: a string representation of item's `field` value

        Raises:
            OnePasswordValueNotFound: if `value` has not been found in the dictionary
        """
        try:
            return self.get_item(item, fields=[field])["value"]
        except KeyError as e:
            raise opex.OnePasswordValueNotFound(f"Value not found. Got error: {e}")

    def get_username(self, item: str) -> str:
        """
        Wrapper around `get_value` to get a username value from an item

        Args:
            item (str): name or UUID of item in Vault
        Returns:
             str: a string representation of username
        """

        return self.get_value(item, "username")

    def get_password(self, item: str) -> str:
        """
        Wrapper around `get_value` to get a password value from an item

        Args:
            item (str): name or UUID of item in Vault
        Returns:
             str: string representation of password
        """

        return self.get_value(item, "password")

    def get_uuid(self, item: str) -> str:
        """
        Retrieve the UUID of an item

        Args:
            item (str): name of the item
        Returns:
            str: a string representation of an item's UUID

        Raises:
            OnePasswordValueNotFound: if `id` has not been found in the dictionary
        """
        try:
            return self.get_item(item)["id"]
        except KeyError as e:
            raise opex.OnePasswordValueNotFound(f"Value not found. Got error: {e}")

    def get_document(self, item: str) -> bytes:
        """
        Retrieve's a document from 1Password in bytes format for later use

        Args:
            item (str): name or UUID of item in Vault
        Returns:
             bytes: a document in bytes format
        """
        cmd = ["op", "document", "get", item, "--vault", self.vault]

        return _run_cmd(cmd).stdout

    def list_items(
        self, categories: List = None, tags: List = None
    ) -> Dict | List[Dict]:
        """
        List all available items within the instantiated vault.
        Entries can be filtered with `categories` and `tags`. By default, these are None.

        Args:
            categories (list): (optional) A list of categories to filter the list with
            tags (list): (optional) A list of tags to filter the list with
        Returns:
            Dict | List[Dict]: either a single item as a dictionary or multiple items as a list of dictionaries
        """

        cmd = ["op", "items", "list", "--vault", self.vault, "--format", "json"]

        if categories:
            cmd += ["--categories", ",".join(categories)]

        if tags:
            cmd += ["--tags", ",".join(tags)]

        return json.loads(_run_cmd(cmd).stdout)
