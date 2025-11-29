"""
Tests for animated GIF support using AnimationManager.
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from decky.managers.animation import AnimationManager


class TestGIFAnimation:
    """Test suite for animated GIF handling."""

    @pytest.fixture
    def animation_manager(self):
        """Create an AnimationManager with mocked renderer."""
        mock_renderer = Mock()
        mock_renderer.render_button_with_icon.return_value = b"rendered_frame"
        return AnimationManager(mock_renderer)

    def test_setup_animated_button_loads_frames(self, animation_manager):
        """Test that animated GIF frames are loaded correctly."""
        # Create a mock animated GIF
        mock_gif = Mock(spec=Image.Image)
        mock_gif.is_animated = True
        mock_gif.n_frames = 3
        mock_gif.info = {"duration": 100}

        frames = []
        for i in range(3):
            frame = Mock(spec=Image.Image)
            frame.copy.return_value = frame
            frames.append(frame)

        mock_gif.seek = Mock()
        mock_gif.copy.side_effect = frames

        with patch("PIL.Image.open", return_value=mock_gif):
            result = animation_manager.setup_animated_button(0, {"icon": "test.gif"}, "test.gif")

        # Verify frames were loaded
        assert result is True
        assert 0 in animation_manager.animated_buttons
        anim_data = animation_manager.animated_buttons[0]
        assert len(anim_data["frames"]) == 3
        assert len(anim_data["durations"]) == 3
        assert anim_data["current_frame"] == 0
        assert "last_update" in anim_data
        assert anim_data["config"] == {"icon": "test.gif"}

    def test_setup_animated_button_handles_static_gif(self, animation_manager):
        """Test handling of non-animated GIF files."""
        mock_gif = Mock(spec=Image.Image)
        mock_gif.is_animated = False

        with patch("PIL.Image.open", return_value=mock_gif):
            result = animation_manager.setup_animated_button(
                0, {"icon": "static.gif"}, "static.gif"
            )

        # Should return False for non-animated GIF
        assert result is False
        assert 0 not in animation_manager.animated_buttons

    def test_update_animations_advances_frames(self, animation_manager):
        """Test that animations advance frames based on duration."""
        # Set up animated button
        animation_manager.animated_buttons[0] = {
            "frames": [Mock(), Mock(), Mock()],
            "durations": [100, 100, 100],  # 100ms per frame
            "current_frame": 0,
            "last_update": time.time() - 0.15,  # 150ms ago
            "config": {"icon": "test.gif"},
        }

        # Trigger update (will advance frame)
        animation_manager.update_animations(Mock())

        # Should have advanced to frame 1
        assert animation_manager.animated_buttons[0]["current_frame"] == 1

    def test_update_animations_loops_to_start(self, animation_manager):
        """Test that animations loop back to frame 0."""
        # Set up animated button at last frame
        animation_manager.animated_buttons[0] = {
            "frames": [Mock(), Mock(), Mock()],
            "durations": [100, 100, 100],
            "current_frame": 2,  # Last frame
            "last_update": time.time() - 0.15,
            "config": {"icon": "test.gif"},
        }

        animation_manager.update_animations(Mock())

        # Should loop back to frame 0
        assert animation_manager.animated_buttons[0]["current_frame"] == 0

    def test_update_page_synchronizes_animations(self, animation_manager):
        """Test that all animations are synchronized when switching pages."""
        # Set up some animated buttons with different frames
        animation_manager.animated_buttons[0] = {
            "frames": [Mock()],
            "durations": [100],
            "current_frame": 5,  # Non-zero frame
            "last_update": 0,
            "config": {"icon": "test1.gif"},
        }
        animation_manager.animated_buttons[1] = {
            "frames": [Mock()],
            "durations": [100],
            "current_frame": 3,  # Different frame
            "last_update": 0,
            "config": {"icon": "test2.gif"},
        }

        # Synchronize animations
        animation_manager.synchronize_animations()

        # All animated buttons should be synchronized to start at frame 0
        current_time = time.time()
        for key, anim_data in animation_manager.animated_buttons.items():
            assert anim_data["current_frame"] == 0
            # last_update should be close to current time
            assert abs(anim_data["last_update"] - current_time) < 1.0

    def test_update_page_clears_previous_animations(self, animation_manager):
        """Test that previous page animations are cleared."""
        # Add some animated buttons
        animation_manager.animated_buttons[0] = {"frames": [Mock()]}
        animation_manager.animated_buttons[1] = {"frames": [Mock()]}

        assert len(animation_manager.animated_buttons) == 2

        # Clear animations
        animation_manager.clear_animations()

        # Should be cleared
        assert len(animation_manager.animated_buttons) == 0

    def test_find_icon_with_absolute_path(self, animation_manager):
        """Test finding icons with absolute paths (tested via PageManager)."""
        # Icon finding is in PageManager now
        # This test is covered by integration tests
        # Just verify AnimationManager can handle absolute paths
        mock_gif = Mock()
        mock_gif.is_animated = True
        mock_gif.n_frames = 1
        mock_gif.info = {"duration": 100}
        mock_gif.copy.return_value = Mock()

        with patch("PIL.Image.open", return_value=mock_gif):
            result = animation_manager.setup_animated_button(
                0, {"icon": "/absolute/path/icon.gif"}, "/absolute/path/icon.gif"
            )

        assert result is True

    def test_find_icon_with_relative_path(self, animation_manager):
        """Test animated button setup with relative paths."""
        # Icon finding is in PageManager now
        # This test verifies AnimationManager works with any path
        mock_gif = Mock()
        mock_gif.is_animated = True
        mock_gif.n_frames = 1
        mock_gif.info = {"duration": 100}
        mock_gif.copy.return_value = Mock()

        with patch("PIL.Image.open", return_value=mock_gif):
            result = animation_manager.setup_animated_button(
                0, {"icon": "icons/test.gif"}, "/home/user/.decky/icons/test.gif"
            )

        assert result is True

    def test_render_animated_frame_uses_current_frame(self, animation_manager):
        """Test that render uses the current animation frame."""
        mock_frame1 = Mock()
        mock_frame2 = Mock()
        mock_frame3 = Mock()

        animation_manager.animated_buttons[0] = {
            "frames": [mock_frame1, mock_frame2, mock_frame3],
            "current_frame": 1,
            "config": {"text": "Test"},
        }

        # Render current frame
        result = animation_manager.render_current_frame(0, {}, Mock())

        # Should have called render_button_with_icon with frame at index 1
        animation_manager.button_renderer.render_button_with_icon.assert_called_once()
        # Check that the correct frame was passed (mock_frame2 at index 1)
        call_args = animation_manager.button_renderer.render_button_with_icon.call_args
        assert call_args[0][3] == mock_frame2
