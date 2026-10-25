"""Tests for stage 1: YAML configuration and its validation."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "src" / "main.py"
VALID_CONFIG = (
    "package: curl\n"
    "repository: https://example.org/alpine/main/x86_64/\n"
    "test_mode: false\n"
    "ascii_tree: true\n"
)


class ConfigTests(unittest.TestCase):
    """Verify valid and invalid configuration files."""

    def setUp(self):
        """Create an isolated directory for each test."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.config_path = self.folder / "config.yaml"

    def start_program(self):
        """Run the CLI with the current test configuration."""
        environment = os.environ.copy()
        environment["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(PROGRAM), str(self.config_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            check=False,
        )

    def run_config(self, content):
        """Write a YAML configuration and run the CLI."""
        self.config_path.write_text(content, encoding="utf-8")
        return self.start_program()

    def check_error(self, content, expected):
        """Check an error message and a nonzero exit code."""
        result = self.run_config(content)
        self.assertEqual(result.returncode, 1)
        self.assertIn(expected, result.stderr)

    def test_valid_config(self):
        """All four valid settings are displayed."""
        result = self.run_config(VALID_CONFIG)
        self.assertEqual(result.returncode, 0)
        self.assertIn("package: curl", result.stdout)
        self.assertIn("test_mode: False", result.stdout)
        self.assertIn("ascii_tree: True", result.stdout)

    def test_missing_config_file(self):
        """An absent configuration file is rejected."""
        result = self.start_program()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Ошибка конфигурации", result.stderr)

    def test_empty_yaml(self):
        """An empty YAML document is rejected."""
        self.check_error("", "YAML должен содержать пары")

    def test_broken_yaml(self):
        """Malformed YAML is rejected."""
        self.check_error("package: [curl\n", "Ошибка конфигурации")

    def test_missing_package(self):
        """A missing package name is rejected."""
        self.check_error(VALID_CONFIG.replace("package: curl\n", ""),
                         "отсутствует параметр 'package'")

    def test_invalid_package(self):
        """A numeric package value is rejected."""
        self.check_error(VALID_CONFIG.replace("curl", "123"),
                         "'package' должен быть непустой строкой")

    def test_missing_repository(self):
        """A missing repository source is rejected."""
        text = VALID_CONFIG.replace(
            "repository: https://example.org/alpine/main/x86_64/\n", ""
        )
        self.check_error(text, "отсутствует параметр 'repository'")

    def test_invalid_repository(self):
        """An invalid URL is rejected in normal mode."""
        self.check_error(VALID_CONFIG.replace(
            "https://example.org/alpine/main/x86_64/", "not-a-url"
        ), "в обычном режиме нужен URL")

    def test_missing_test_mode(self):
        """A missing test mode is rejected."""
        self.check_error(VALID_CONFIG.replace("test_mode: false\n", ""),
                         "отсутствует параметр 'test_mode'")

    def test_invalid_test_mode(self):
        """Test mode must be a YAML Boolean."""
        config = VALID_CONFIG.replace("test_mode: false", "test_mode: hi")
        self.check_error(config, "'test_mode' должен быть true или false")

    def test_missing_ascii_tree(self):
        """A missing ASCII setting is rejected."""
        self.check_error(VALID_CONFIG.replace("ascii_tree: true\n", ""),
                         "отсутствует параметр 'ascii_tree'")

    def test_invalid_ascii_tree(self):
        """ASCII setting must be a YAML Boolean."""
        config = VALID_CONFIG.replace("ascii_tree: true", "ascii_tree: 5")
        self.check_error(config, "'ascii_tree' должен быть true или false")

    def test_url_in_test_mode(self):
        """A URL is not accepted in test mode."""
        config = VALID_CONFIG.replace("test_mode: false", "test_mode: true")
        self.check_error(config, "в тестовом режиме нужен путь к файлу")

    def test_missing_test_repository(self):
        """An absent test repository file is rejected."""
        text = (
            "package: A\n"
            "repository: missing_repo.txt\n"
            "test_mode: true\n"
            "ascii_tree: false\n"
        )
        self.check_error(text, "тестовый файл не найден")

    def test_valid_test_repository(self):
        """An existing test repository path is accepted."""
        source = self.folder / "repository.txt"
        source.write_text("A: B\n", encoding="utf-8")
        text = (
            "package: A\n"
            f"repository: '{source.as_posix()}'\n"
            "test_mode: true\n"
            "ascii_tree: false\n"
        )
        result = self.run_config(text)
        self.assertEqual(result.returncode, 0)
        self.assertIn("test_mode: True", result.stdout)


if __name__ == "__main__":
    unittest.main()
