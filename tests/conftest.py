"""
Pytest configuration and fixtures
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "device": {
            "brightness": 75
        },
        "styles": {
            "default": {
                "font": "DejaVu Sans",
                "font_size": 14,
                "text_color": "#FFFFFF",
                "background_color": "#000000",
                "text_align": "bottom",
                "text_offset": 0
            }
        },
        "pages": {
            "main": {
                "name": "Main",
                "buttons": {
                    1: {
                        "text": "Test",
                        "style": "default",
                        "action": {
                            "type": "command",
                            "command": "echo test"
                        }
                    },
                    2: {
                        "icon": "test.png",
                        "action": {
                            "type": "application",
                            "app": "test-app"
                        }
                    },
                    3: {
                        "text": "Page 2",
                        "action": {
                            "type": "page",
                            "page": "secondary"
                        }
                    }
                }
            },
            "secondary": {
                "name": "Secondary",
                "buttons": {}
            }
        }
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """Create a temporary config file"""
    config_path = tmp_path / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def mock_deck():
    """Mock Stream Deck device"""
    deck = MagicMock()
    deck.is_visual.return_value = True
    deck.is_open.return_value = True
    deck.key_count.return_value = 15
    deck.get_serial_number.return_value = "TEST123"
    deck.deck_type.return_value = "Stream Deck Original"
    deck.key_image_format.return_value = {
        'size': (72, 72),
        'format': 'BMP',
        'flip': (True, False),
        'rotation': 0
    }
    return deck


@pytest.fixture
def mock_platform():
    """Mock platform implementation"""
    platform = Mock()
    platform.name = "test"
    platform.detect.return_value = True
    platform.is_screen_locked.return_value = False
    platform.launch_application.return_value = True
    return platform


@pytest.fixture
def action_context(mock_deck, mock_platform):
    """Mock action context"""
    context = Mock()
    context.controller = Mock()
    context.controller.deck = mock_deck
    context.platform = mock_platform
    context.button_config = {}
    context.key_index = 0
    return context


@pytest.fixture(autouse=True)
def no_subprocess_calls(monkeypatch):
    """Prevent actual subprocess calls during testing"""
    mock_popen = Mock()
    mock_popen.returncode = 0
    monkeypatch.setattr("subprocess.Popen", Mock(return_value=mock_popen))
    monkeypatch.setattr("subprocess.run", Mock(return_value=Mock(returncode=0)))


@pytest.fixture
def sample_image():
    """Create a sample test image"""
    from PIL import Image
    img = Image.new('RGB', (72, 72), color='red')
    return img