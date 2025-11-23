"""
Tests for action system - focusing on preventing regressions
"""

from unittest.mock import Mock, call, patch

import pytest

from decky.actions.application import ApplicationAction
from decky.actions.base import ActionContext, BaseAction
from decky.actions.command import CommandAction
from decky.actions.registry import ActionRegistry


class TestActionRegistry:
    """Test action registry functionality"""

    def test_register_action(self):
        """Test registering a new action type"""
        registry = ActionRegistry()

        class TestAction(BaseAction):
            action_type = "test"

            def execute(self, context, config):
                return True

        registry.register(TestAction)
        assert "test" in registry.list_actions()
        assert registry.get_action("test") is not None

    def test_register_duplicate_warns(self, caplog):
        """Test that registering duplicate action types warns"""
        registry = ActionRegistry()

        class TestAction1(BaseAction):
            action_type = "test"

            def execute(self, context, config):
                return True

        class TestAction2(BaseAction):
            action_type = "test"

            def execute(self, context, config):
                return False

        registry.register(TestAction1)
        registry.register(TestAction2)

        assert "Overwriting existing action type: test" in caplog.text

    def test_platform_support_check(self):
        """Test platform support checking"""
        registry = ActionRegistry()

        class LinuxOnlyAction(BaseAction):
            action_type = "linux_only"
            supported_platforms = ["linux", "kde"]

            def execute(self, context, config):
                return True

        registry.register(LinuxOnlyAction)
        assert registry.is_supported("linux_only", "kde")
        assert registry.is_supported("linux_only", "linux")
        assert not registry.is_supported("linux_only", "windows")


class TestCommandAction:
    """Test command execution action"""

    def test_execute_command_success(self, action_context):
        """Test successful command execution"""
        action = CommandAction()
        config = {"command": "echo test"}

        with patch("subprocess.Popen") as mock_popen:
            result = action.execute(action_context, config)
            assert result is True
            mock_popen.assert_called_once_with("echo test", shell=True)

    def test_execute_command_missing_parameter(self, action_context):
        """Test command execution with missing parameter"""
        action = CommandAction()
        config = {}

        result = action.execute(action_context, config)
        assert result is False

    def test_validate_config(self):
        """Test configuration validation"""
        action = CommandAction()
        assert action.validate_config({"command": "test"}) is True
        assert action.validate_config({}) is False

    def test_command_execution_failure(self, action_context):
        """Test handling of command execution failure"""
        action = CommandAction()
        config = {"command": "failing_command"}

        with patch("subprocess.Popen", side_effect=Exception("Command failed")):
            result = action.execute(action_context, config)
            assert result is False


class TestApplicationAction:
    """Test application launcher action"""

    def test_launch_with_platform(self, action_context):
        """Test launching application using platform-specific method"""
        action = ApplicationAction()
        config = {"app": "test-app"}

        result = action.execute(action_context, config)
        assert result is True
        action_context.platform.launch_application.assert_called_once_with("test-app")

    def test_launch_fallback_to_script(self, action_context):
        """Test fallback to launcher script"""
        action = ApplicationAction()
        config = {"app": "test-app"}
        action_context.platform = None

        with patch("os.path.exists", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                result = action.execute(action_context, config)
                assert result is True
                assert mock_popen.called

    def test_launch_direct_fallback(self, action_context):
        """Test direct execution fallback"""
        action = ApplicationAction()
        config = {"app": "test-app"}
        action_context.platform = None

        with patch("os.path.exists", return_value=False):
            with patch("subprocess.Popen") as mock_popen:
                result = action.execute(action_context, config)
                assert result is True
                mock_popen.assert_called_once_with("test-app", shell=True)

    def test_missing_app_parameter(self, action_context):
        """Test handling missing app parameter"""
        action = ApplicationAction()
        config = {}

        result = action.execute(action_context, config)
        assert result is False


class TestActionCompatibility:
    """Test backward compatibility and regression prevention"""

    def test_action_parameters_unchanged(self):
        """Ensure action parameters haven't changed (prevents breaking configs)"""
        # This test ensures we don't accidentally change required parameters
        command_action = CommandAction()
        assert command_action.get_required_params() == ["command"]

        app_action = ApplicationAction()
        assert app_action.get_required_params() == ["app"]

    def test_action_types_unchanged(self):
        """Ensure action type identifiers haven't changed"""
        # This prevents breaking existing configurations
        assert CommandAction.action_type == "command"
        assert ApplicationAction.action_type == "application"

    def test_action_execution_non_blocking(self, action_context):
        """Ensure actions don't block (regression test for freezing issue)"""
        import time

        action = CommandAction()
        config = {"command": "sleep 10"}

        start_time = time.time()
        with patch("subprocess.Popen") as mock_popen:
            # Popen should return immediately
            result = action.execute(action_context, config)
            elapsed = time.time() - start_time

            assert result is True
            assert elapsed < 1.0  # Should complete almost instantly
            mock_popen.assert_called_once()
