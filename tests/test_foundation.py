"""Verify credential boundaries and render the real shell without Google access."""

# 1. Use the standard library and Streamlit's installed test harness.
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.runtime.secrets import Secrets
from streamlit.testing.v1 import AppTest

from music_agent.config import resolve_google_api_key

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


# 2. Check real missing-file behavior and precedence with synthetic credentials.
class ConfigurationTests(unittest.TestCase):
    def test_missing_secrets_file_and_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            secrets = Secrets()
            with patch("streamlit.config.get_option", return_value=[
                str(Path(directory) / "missing.toml")
            ]):
                self.assertFalse(resolve_google_api_key(secrets, {}).configured)

    def test_secrets_precede_environment_without_leaking_in_repr(self) -> None:
        result = resolve_google_api_key(
            {"GOOGLE_API_KEY": "synthetic-secret"},
            {"GOOGLE_API_KEY": "synthetic-environment"},
        )
        self.assertEqual(result.api_key, "synthetic-secret")
        self.assertEqual(result.source, "Streamlit Secrets")
        self.assertNotIn("synthetic-secret", repr(result))

    def test_blank_or_invalid_secret_falls_back_to_environment(self) -> None:
        for value in (None, "", "   ", 123):
            with self.subTest(value=value):
                result = resolve_google_api_key(
                    {"GOOGLE_API_KEY": value},
                    {"GOOGLE_API_KEY": "synthetic-environment"},
                )
                self.assertEqual(result.api_key, "synthetic-environment")
                self.assertEqual(result.source, "environment")

    def test_unreadable_secrets_fall_back_without_exception_details(self) -> None:
        from unittest.mock import Mock

        secrets = Mock()
        secrets.get.side_effect = ValueError("private configuration detail")
        result = resolve_google_api_key(secrets, {})
        self.assertFalse(result.configured)
        self.assertNotIn("private configuration detail", repr(result))


# 3. Exercise app execution and reruns, including the configured-key UI boundary.
class ShellTests(unittest.TestCase):
    def test_no_key_shell_and_rerun(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch("streamlit.secrets", {}):
            app = AppTest.from_file(str(APP_PATH)).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.header[0].value, "Let’s find your groove")
            self.assertIsNone(app.session_state["profile"])
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.header[0].value, "Let’s find your groove")

    def test_configured_key_is_not_rendered(self) -> None:
        key = "synthetic-shell-secret"
        with patch.dict(os.environ, {}, clear=True), patch(
            "streamlit.secrets", {"GOOGLE_API_KEY": key}
        ):
            app = AppTest.from_file(str(APP_PATH)).run()
            self.assertFalse(app.exception)
            self.assertEqual(app.header[0].value, "Let’s find your groove")
            self.assertNotIn(key, str(app))


if __name__ == "__main__":
    unittest.main()
