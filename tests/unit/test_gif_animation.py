"""
Tests for animated GIF support in the controller.
"""

import pytest
import time
from unittest.mock import Mock, MagicMock, patch
from PIL import Image
from decky.controller import DeckyController


class TestGIFAnimation:
    """Test suite for animated GIF handling."""

    @pytest.fixture
    def controller(self):
        """Create a controller instance with mocked dependencies."""
        with patch('decky.controller.ConfigLoader'), \
             patch('decky.controller.DeckManager'), \
             patch('decky.controller.ButtonRenderer'), \
             patch('decky.controller.registry'), \
             patch('decky.controller.detect_platform'):
            controller = DeckyController('/test/config.yaml')
            controller.config = {
                'device': {'brightness': 75},
                'styles': {'default': {}},
                'pages': {
                    'main': {
                        'buttons': {
                            1: {'icon': 'test.gif', 'text': 'Test'},
                            2: {'icon': 'static.png', 'text': 'Static'}
                        }
                    }
                }
            }
            # Mock deck
            mock_deck = Mock()
            mock_deck.key_count.return_value = 15
            mock_deck.key_image_format.return_value = {'size': (72, 72)}
            controller.deck = mock_deck
            return controller

    def test_setup_animated_button_loads_frames(self, controller):
        """Test that animated GIF frames are loaded correctly."""
        # Create a mock animated GIF
        mock_gif = Mock(spec=Image.Image)
        mock_gif.is_animated = True
        mock_gif.n_frames = 3
        mock_gif.info = {'duration': 100}

        frames = []
        for i in range(3):
            frame = Mock(spec=Image.Image)
            frame.copy.return_value = frame
            frames.append(frame)

        mock_gif.seek = Mock()
        mock_gif.copy.side_effect = frames

        with patch('PIL.Image.open', return_value=mock_gif):
            controller._setup_animated_button(0, {'icon': 'test.gif'}, 'test.gif')

        # Verify frames were loaded
        assert 0 in controller.animated_buttons
        anim_data = controller.animated_buttons[0]
        assert len(anim_data['frames']) == 3
        assert len(anim_data['durations']) == 3
        assert anim_data['current_frame'] == 0
        assert 'last_update' in anim_data
        assert anim_data['config'] == {'icon': 'test.gif'}

    def test_setup_animated_button_handles_static_gif(self, controller):
        """Test handling of non-animated GIF files."""
        mock_gif = Mock(spec=Image.Image)
        mock_gif.is_animated = False

        with patch('PIL.Image.open', return_value=mock_gif):
            controller._setup_animated_button(0, {'icon': 'static.gif'}, 'static.gif')

        # Should not add to animated_buttons
        assert 0 not in controller.animated_buttons

    def test_update_animations_advances_frames(self, controller):
        """Test that animations advance frames based on duration."""
        # Set up animated button
        controller.animated_buttons[0] = {
            'frames': [Mock(), Mock(), Mock()],
            'durations': [100, 100, 100],  # 100ms per frame
            'current_frame': 0,
            'last_update': time.time() - 0.15,  # 150ms ago
            'config': {'icon': 'test.gif'}
        }

        with patch.object(controller, '_render_animated_frame', return_value=b'image'):
            controller._update_animations()

        # Should have advanced to frame 1
        assert controller.animated_buttons[0]['current_frame'] == 1

    def test_update_animations_loops_to_start(self, controller):
        """Test that animations loop back to frame 0."""
        # Set up animated button at last frame
        controller.animated_buttons[0] = {
            'frames': [Mock(), Mock(), Mock()],
            'durations': [100, 100, 100],
            'current_frame': 2,  # Last frame
            'last_update': time.time() - 0.15,
            'config': {'icon': 'test.gif'}
        }

        with patch.object(controller, '_render_animated_frame', return_value=b'image'):
            controller._update_animations()

        # Should loop back to frame 0
        assert controller.animated_buttons[0]['current_frame'] == 0

    def test_update_page_synchronizes_animations(self, controller):
        """Test that all animations are synchronized when switching pages."""
        # Set up page config with a GIF button
        controller.config['pages']['main']['buttons'][1] = {
            'icon': 'test.gif',
            'text': 'Test'
        }

        # Mock finding GIF files
        with patch.object(controller, '_find_icon') as mock_find:
            mock_find.side_effect = lambda path: f'/path/{path}' if path.endswith('.gif') else None

            # Mock setup for animated buttons
            with patch.object(controller, '_setup_animated_button') as mock_setup:
                # Create mock animated data
                def setup_side_effect(key, config, path):
                    controller.animated_buttons[key] = {
                        'frames': [Mock()],
                        'durations': [100],
                        'current_frame': 5,  # Non-zero frame
                        'last_update': 0,
                        'config': config
                    }

                mock_setup.side_effect = setup_side_effect

                # Mock render_animated_frame so it doesn't fail
                with patch.object(controller, '_render_animated_frame', return_value=b'image'):
                    controller._update_page()

        # All animated buttons should be synchronized to start at frame 0
        current_time = time.time()
        for key, anim_data in controller.animated_buttons.items():
            assert anim_data['current_frame'] == 0
            # last_update should be close to current time
            assert abs(anim_data['last_update'] - current_time) < 1.0

    def test_update_page_clears_previous_animations(self, controller):
        """Test that previous page animations are cleared."""
        # Add some animated buttons
        controller.animated_buttons[0] = {'frames': [Mock()]}
        controller.animated_buttons[1] = {'frames': [Mock()]}

        assert len(controller.animated_buttons) == 2

        controller._update_page()

        # Should be cleared (no GIFs in current config)
        assert len(controller.animated_buttons) == 0

    def test_find_icon_with_absolute_path(self, controller):
        """Test finding icons with absolute paths."""
        with patch('os.path.exists', return_value=True):
            result = controller._find_icon('/absolute/path/icon.gif')

        assert result == '/absolute/path/icon.gif'

    def test_find_icon_with_relative_path(self, controller):
        """Test finding icons relative to ~/.decky/."""
        with patch('os.path.exists') as mock_exists, \
             patch('os.path.expanduser') as mock_expand:
            mock_expand.side_effect = lambda x: x.replace('~', '/home/user')
            mock_exists.side_effect = lambda path: 'decky/icons' in path

            result = controller._find_icon('icons/test.gif')

        assert result == '/home/user/.decky/icons/test.gif'

    def test_render_animated_frame_uses_current_frame(self, controller):
        """Test that render uses the current animation frame."""
        mock_frame = Mock()
        controller.animated_buttons[0] = {
            'frames': [Mock(), mock_frame, Mock()],
            'current_frame': 1,
            'config': {'text': 'Test'}
        }

        with patch.object(controller.button_renderer, 'render_button_with_icon') as mock_render:
            controller._render_animated_frame(0)

        # Should use the current frame (index 1)
        mock_render.assert_called_once()
        assert mock_render.call_args[0][3] == mock_frame