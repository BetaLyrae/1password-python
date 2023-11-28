import unittest
import subprocess

from packaging.version import Version
from onepassword import onepassword

TAG = "coffee"  # Change with the name of a tag in your own vault, I made a dummy tag called 'coffee'.
ITEM = "Coffee"  # Change with the name of an item in your own vault, I made a dummy entry called "Coffee".


class IntegrationTestListItems(unittest.TestCase):
    def test_list_items_integration(self):
        try:
            subprocess.run(["op", "--version"], check=True, capture_output=True)
        except FileNotFoundError:
            self.skipTest("1Password CLI 'op' not found. Skipping integration test.")

        op = onepassword.OnePassword("Private")

        items_without_filters = op.list_items(categories=[], tags=[])
        self.assertTrue(isinstance(items_without_filters, list))

        items_with_filters = op.list_items(categories=["Login"], tags=[TAG])
        self.assertTrue(isinstance(items_with_filters, list))


class IntegrationTestGetItem(unittest.TestCase):
    def test_get_item_integration(self):
        try:
            subprocess.run(["op", "--version"], check=True, capture_output=True)
        except FileNotFoundError:
            self.skipTest("1Password CLI 'op' not found. Skipping integration test.")

        op = onepassword.OnePassword("Private")

        item_without_fields = op.get_item(ITEM)
        self.assertTrue(isinstance(item_without_fields, (dict, list)))

        item_with_fields = op.get_item(ITEM, fields=["username"])
        self.assertTrue(isinstance(item_with_fields, (dict, list)))


class IntegrationTestGetOPCLIVersion(unittest.TestCase):
    def test_get_op_cli_version_integration(self):
        try:
            subprocess.run(["op", "--version"], check=True, capture_output=True)
        except FileNotFoundError:
            self.skipTest("1Password CLI 'op' not found. Skipping integration test.")

        try:
            version = onepassword.get_op_cli_version()
            self.assertTrue(isinstance(version, Version))
        except onepassword.opex.OnePasswordCLINotFound as e:
            self.fail(f"Integration test failed: {e}")


class IntegrationTestGetValue(unittest.TestCase):
    def test_get_value_integration(self):
        try:
            subprocess.run(["op", "--version"], check=True, capture_output=True)
        except FileNotFoundError:
            self.skipTest("1Password CLI 'op' not found. Skipping integration test.")

        op = onepassword.OnePassword("Private")

        try:
            field_name = "username"
            value = op.get_value(ITEM, field_name)
            self.assertTrue(isinstance(value, str))
            self.assertEqual(value, "some_username@example.com")
        except onepassword.opex.OnePasswordValueNotFound as e:
            self.fail(f"Integration test failed: {e}")
