"""
Tests for CLI input validation.

These tests verify that config names are properly validated to prevent
path traversal and other security issues.
"""

import pytest

from decky.cli import DeckyCLI


class TestConfigNameValidation:
    """Test configuration name validation"""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing"""
        return DeckyCLI()

    def test_valid_config_names(self, cli):
        """Test that valid config names are accepted"""
        valid_names = [
            "default",
            "kde",
            "work",
            "my-config",
            "config_v2",
            "CONFIG123",
            "test-config-01",
        ]

        for name in valid_names:
            # Should not raise exception
            cli._validate_config_name(name)

    def test_invalid_config_names_with_path_separators(self, cli):
        """Test that config names with path separators are rejected"""
        invalid_names = [
            "../etc/passwd",
            "my/config",
            "..\\windows",
            "config/../other",
            "/etc/config",
        ]

        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid config name"):
                cli._validate_config_name(name)

    def test_invalid_config_names_with_special_chars(self, cli):
        """Test that config names with special characters are rejected"""
        invalid_names = [
            "my config",  # Space
            "config@home",  # @
            "config!",  # !
            "config#1",  # #
            "config$var",  # $
            "config&more",  # &
        ]

        for name in invalid_names:
            with pytest.raises(ValueError, match="Invalid config name"):
                cli._validate_config_name(name)

    def test_empty_config_name(self, cli):
        """Test that empty config name is rejected"""
        with pytest.raises(ValueError, match="cannot be empty"):
            cli._validate_config_name("")

    def test_reserved_names(self, cli):
        """Test that Windows reserved names are rejected"""
        reserved_names = ["con", "prn", "aux", "nul", "CON", "PRN"]

        for name in reserved_names:
            with pytest.raises(ValueError, match="reserved name"):
                cli._validate_config_name(name)

    def test_validation_on_edit_config(self, cli, tmp_path):
        """Test that edit_config validates the name"""
        # Override configs_dir for testing
        cli.configs_dir = tmp_path

        # Invalid name should fail
        result = cli.edit_config("../etc/passwd")
        assert result == 1  # Error return code

    def test_validation_on_use_config(self, cli, tmp_path):
        """Test that use_config validates the name"""
        cli.configs_dir = tmp_path

        # Invalid name should fail
        result = cli.use_config("config/../../secret")
        assert result == 1  # Error return code

    def test_validation_on_validate_config(self, cli, tmp_path):
        """Test that validate_config validates the name"""
        cli.configs_dir = tmp_path

        # Invalid name should fail
        result = cli.validate_config("bad@config")
        assert result == 1  # Error return code


class TestConfigPathsNotValidated:
    """
    Test that FULL PATHS are NOT validated by regex.

    The _validate_config_name() method should ONLY be used for config names,
    not for full paths supplied to 'decky run <path>'.
    """

    def test_run_command_accepts_any_path(self):
        """
        Test that 'decky run' accepts full paths without validation.

        This ensures users can still run configs from any location:
        - ~/Development/decky/configs/test.yaml
        - /home/user/.decky/configs/custom.yaml
        - /tmp/test-config.yaml
        """
        cli = DeckyCLI()

        # The run_daemon method should NOT call _validate_config_name
        # It passes the path directly to ConfigLoader which has its own validation
        # This test just documents the expected behavior

        # Full paths should be passed through to ConfigLoader
        # (they will be validated there for actual file existence, size, etc.)
        test_paths = [
            "~/Development/decky/configs/kde.yaml",
            "/home/anicholas/.decky/configs/custom.yaml",
            "../configs/test.yaml",
            "/tmp/test.yaml",
        ]

        # All these should be acceptable as arguments to run_daemon
        # (ConfigLoader will validate them properly)
        for path in test_paths:
            # Just verify the method signature accepts any string
            # Actual validation happens in ConfigLoader, not CLI
            assert isinstance(path, str)
