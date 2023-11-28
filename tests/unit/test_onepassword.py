import unittest
import json

from unittest.mock import patch, MagicMock
from packaging.version import Version

from onepassword import onepassword


class TestGetOpCliVersion(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_op_cli_version_success(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(
            stdout="2.23.0\n", stderr="", returncode=0
        )

        result = onepassword.get_op_cli_version()

        mock_subprocess_run.assert_called_once_with(
            ["op", "--version"], capture_output=True, text=True
        )
        self.assertIsInstance(result, Version)
        self.assertEqual(result, Version("2.23.0"))

    @patch("subprocess.run")
    def test_get_op_cli_version_file_not_found(self, mock_subprocess_run):
        # Mock subprocess.run to raise a FileNotFoundError
        mock_subprocess_run.side_effect = FileNotFoundError(
            "No such file or directory: 'op'"
        )

        # Call the function to test and expect an opex.OnepasswordCLINotFound exception
        with self.assertRaises(onepassword.opex.OnePasswordCLINotFound):
            onepassword.get_op_cli_version()

        # Assert that the subprocess.run was called with the correct arguments
        mock_subprocess_run.assert_called_once_with(
            ["op", "--version"], capture_output=True, text=True
        )


class TestRunCmd(unittest.TestCase):
    @patch("subprocess.run")
    def test_run_cmd(self, mock_subprocess_run):
        # Mock subprocess.run to return a known CompletedProcess object
        mock_subprocess_run.return_value = MagicMock(
            stdout="2.23.0\n", stderr="", returncode=0
        )

        # Call the function to test
        cmd = ["op", "--version"]
        result = onepassword._run_cmd(cmd)

        # Assert that the subprocess.run was called with the correct arguments
        mock_subprocess_run.assert_called_once_with(cmd, capture_output=True)

        # Assert that the returned value is the expected CompletedProcess object
        self.assertEqual(result.stdout, "2.23.0\n")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 0)

    @patch("subprocess.run")
    def test_run_cmd_error(self, mock_subprocess_run):
        mock_subprocess_run.return_value = MagicMock(
            stdout=b"", stderr=b"I have failed", returncode=1
        )

        with self.assertRaises(onepassword.opex.OnePasswordRuntimeError):
            onepassword._run_cmd(["nonexistent", "please", "fail"])

        mock_subprocess_run.assert_called_once_with(
            ["nonexistent", "please", "fail"], capture_output=True
        )


class TestGetItem(unittest.TestCase):
    @patch("onepassword.onepassword._run_cmd")
    def test_get_item_success_without_fields(self, mock_run_cmd):
        expected_response = {
            "category": "LOGIN",
            "id": "id123456789",
            "fields": [
                {
                    "id": "username",
                    "label": "username",
                    "purpose": "USERNAME",
                    "reference": "op://Private/Foo/username",
                    "type": "STRING",
                    "value": "bar@example.com",
                },
                {
                    "id": "password",
                    "label": "password",
                    "purpose": "PASSWORD",
                    "reference": "op://Private/Foo/password",
                    "type": "STRING",
                    "value": "some_secret_password",
                },
            ],
        }
        mock_run_cmd.return_value = MagicMock(
            stdout=json.dumps(expected_response), stderr="", returncode=0
        )

        op = onepassword.OnePassword("Private")

        item_name = "Foo"
        result = op.get_item(item_name)

        mock_run_cmd.assert_called_once_with(
            ["op", "item", "get", item_name, "--format", "json", "--vault", "Private"]
        )

        self.assertEqual(result, expected_response)

    @patch("onepassword.onepassword._run_cmd")
    def test_get_item_success_with_fields(self, mock_run_cmd):
        expected_response = {
            "category": "LOGIN",
            "id": "id123456789",
            "fields": [
                {
                    "id": "username",
                    "label": "username",
                    "purpose": "USERNAME",
                    "reference": "op://Private/Foo/username",
                    "type": "STRING",
                    "value": "bar@example.com",
                }
            ],
        }
        mock_run_cmd.return_value = MagicMock(
            stdout=json.dumps(expected_response), stderr="", returncode=0
        )

        op = onepassword.OnePassword("Private")

        item_name = "Foo"
        fields = ["username"]
        result = op.get_item(item_name, fields)

        mock_run_cmd.assert_called_once_with(
            [
                "op",
                "item",
                "get",
                item_name,
                "--format",
                "json",
                "--vault",
                "Private",
                "--fields",
                "label=username",
            ]
        )

        self.assertEqual(result, expected_response)

    @patch("onepassword.onepassword._run_cmd")
    def test_get_item_json_error(self, mock_run_cmd):
        invalid_json_response = "Invalid JSON"
        mock_run_cmd.return_value = MagicMock(
            stdout=invalid_json_response, stderr="", returncode=0
        )

        op = onepassword.OnePassword("Private")

        with self.assertRaises(onepassword.opex.OnePasswordJSONError):
            op.get_item("Foo")

        mock_run_cmd.assert_called_once()


class TestGetUUID(unittest.TestCase):
    @patch("onepassword.OnePassword.get_item")
    def test_get_uuid_success(self, mock_get_item):
        expected_item = {"id": "some_valid_uuid"}
        mock_get_item.return_value = expected_item

        op = onepassword.OnePassword("Private")

        result = op.get_uuid("foo")

        mock_get_item.assert_called_once_with("foo")

        self.assertIsInstance(result, str)
        self.assertEqual(result, "some_valid_uuid")

    @patch("onepassword.OnePassword.get_item")
    def test_get_uuid_key_error(self, mock_get_item):
        invalid_item = {"nonexistent": 1}
        mock_get_item.return_value = invalid_item

        op = onepassword.OnePassword("Private")

        with self.assertRaises(onepassword.opex.OnePasswordValueNotFound):
            op.get_uuid("Foo")

        mock_get_item.assert_called_once_with("Foo")


class TestGetValue(unittest.TestCase):
    @patch("onepassword.OnePassword.get_item")
    def test_get_value_success(self, mock_get_item):
        expected_item = {"value": "bar"}
        mock_get_item.return_value = expected_item

        op = onepassword.OnePassword("Private")

        result = op.get_value("foo", field="value")

        mock_get_item.assert_called_once_with("foo", fields=["value"])

        self.assertEqual(result, "bar")

    @patch("onepassword.OnePassword.get_item")
    def test_get_value_key_error(self, mock_get_item):
        invalid_item = {"other_key": "other_value"}
        mock_get_item.return_value = invalid_item

        op = onepassword.OnePassword("Private")

        with self.assertRaises(onepassword.opex.OnePasswordValueNotFound):
            op.get_value("foo", "bar")

        mock_get_item.assert_called_once_with("foo", fields=["bar"])


class TestGetUsername(unittest.TestCase):
    @patch("onepassword.OnePassword.get_value")
    def test_get_username_success(self, mock_get_value):
        expected_username = "bar@example.com"
        mock_get_value.return_value = expected_username

        op = onepassword.OnePassword("Private")

        result = op.get_username("foo")

        mock_get_value.assert_called_once_with("foo", "username")

        self.assertEqual(result, expected_username)


class TestGetPassword(unittest.TestCase):
    @patch("onepassword.OnePassword.get_value")
    def test_get_password_success(self, mock_get_value):
        expected_password = "some_secret_string"
        mock_get_value.return_value = expected_password

        op = onepassword.OnePassword("Private")

        result = op.get_password("foo")

        mock_get_value.assert_called_once_with("foo", "password")

        self.assertEqual(result, expected_password)


class TestGetDocument(unittest.TestCase):
    @patch("onepassword.onepassword._run_cmd")
    def test_get_document_success(self, mock_run_cmd):
        expected_document_content = b"Test document"
        mock_run_cmd.return_value = MagicMock(
            stdout=expected_document_content, stderr=b"", returncode=0
        )

        op = onepassword.OnePassword("Private")

        result = op.get_document("foo")

        mock_run_cmd.assert_called_once_with(
            ["op", "document", "get", "foo", "--vault", "Private"]
        )

        self.assertEqual(result, expected_document_content)


class TestListVaults(unittest.TestCase):
    @patch("onepassword.onepassword._run_cmd")
    def test_list_vaults_success(self, mock_run_cmd):
        expected_vaults = [
            {"id": "vault1", "name": "Vault 1"},
            {"id": "vault2", "name": "Vault 2"},
        ]
        mock_run_cmd.return_value = MagicMock(
            stdout=json.dumps(expected_vaults), stderr=b"", returncode=0
        )

        result = onepassword.list_vaults()

        mock_run_cmd.assert_called_once_with(
            ["op", "vault", "list", "--format", "json"]
        )

        self.assertEqual(result, expected_vaults)


class TestListItems(unittest.TestCase):
    @patch("onepassword.onepassword._run_cmd")
    def test_list_items_no_filters(self, mock_run_cmd):
        expected_items = [
            {"id": "item1", "name": "Item 1"},
            {"id": "item2", "name": "Item 2"},
        ]
        mock_run_cmd.return_value = MagicMock(
            stdout=json.dumps(expected_items), stderr=b"", returncode=0
        )

        op = onepassword.OnePassword("Private")

        result = op.list_items(categories=[], tags=[])

        mock_run_cmd.assert_called_once_with(
            ["op", "items", "list", "--vault", "Private", "--format", "json"]
        )

        self.assertEqual(result, expected_items)

    @patch("onepassword.onepassword._run_cmd")
    def test_list_items_with_filters(self, mock_run_cmd):
        expected_items = [{"id": "item1", "name": "Item 1"}]
        mock_run_cmd.return_value = MagicMock(
            stdout=json.dumps(expected_items), stderr=b"", returncode=0
        )

        op = onepassword.OnePassword("Private")

        result = op.list_items(
            categories=["Login", "Password"], tags=["some_tag", "another_tag"]
        )

        mock_run_cmd.assert_called_once_with(
            [
                "op",
                "items",
                "list",
                "--vault",
                "Private",
                "--format",
                "json",
                "--categories",
                "Login,Password",
                "--tags",
                "some_tag,another_tag",
            ]
        )

        self.assertEqual(result, expected_items)
