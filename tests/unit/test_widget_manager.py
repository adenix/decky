"""
Tests for WidgetManager and WidgetRegistry.
"""

import time
import unittest
from unittest.mock import MagicMock, Mock, patch

from decky.managers.widget import WidgetManager, WidgetRegistry
from decky.widgets.base import BaseWidget


class MockWidget(BaseWidget):
    """Mock widget for testing."""

    widget_type = "mock"
    update_interval = 1.0

    def __init__(self, config):
        super().__init__(config)
        self.fetch_called = False
        self.render_called = False

    def fetch_data(self):
        self.fetch_called = True
        return {"value": 42}

    def render_text(self, data):
        self.render_called = True
        return f"Test: {data['value']}"

    def get_fallback_data(self):
        return {"value": 0}


class InvalidWidget:
    """Invalid widget that doesn't inherit from BaseWidget."""

    widget_type = "invalid"


class TestWidgetRegistry(unittest.TestCase):
    """Test WidgetRegistry functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.registry = WidgetRegistry()

    def test_register_valid_widget(self):
        """Test registering a valid widget."""
        self.registry.register(MockWidget)
        self.assertIn("mock", self.registry.list_widgets())
        self.assertEqual(self.registry.get_widget_class("mock"), MockWidget)

    def test_register_invalid_widget(self):
        """Test that registering invalid widget raises TypeError."""
        with self.assertRaises(TypeError):
            self.registry.register(InvalidWidget)

    def test_register_duplicate_widget(self):
        """Test registering duplicate widget type."""
        self.registry.register(MockWidget)
        # Should log warning but succeed
        self.registry.register(MockWidget)
        self.assertEqual(self.registry.get_widget_class("mock"), MockWidget)

    def test_get_nonexistent_widget(self):
        """Test getting a widget that doesn't exist."""
        result = self.registry.get_widget_class("nonexistent")
        self.assertIsNone(result)

    def test_list_widgets_empty(self):
        """Test listing widgets when registry is empty."""
        self.assertEqual(self.registry.list_widgets(), [])

    def test_list_widgets(self):
        """Test listing registered widgets."""
        self.registry.register(MockWidget)
        widgets = self.registry.list_widgets()
        self.assertIsInstance(widgets, list)
        self.assertIn("mock", widgets)


class TestWidgetManager(unittest.TestCase):
    """Test WidgetManager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.button_renderer = MagicMock()
        self.manager = WidgetManager(self.button_renderer)
        self.manager.widget_registry.register(MockWidget)

        # Mock deck
        self.deck = MagicMock()
        self.deck.key_image_format.return_value = {"size": (72, 72)}

    def test_init(self):
        """Test WidgetManager initialization."""
        self.assertIsNotNone(self.manager.widget_registry)
        self.assertEqual(len(self.manager.active_widgets), 0)
        self.assertEqual(self.manager._total_cache_size, 0)

    def test_setup_widget_button_success(self):
        """Test successful widget setup."""
        button_config = {
            "widget": {"type": "mock"},
            "text": "Original"
        }
        
        result = self.manager.setup_widget_button(0, button_config, {})
        
        self.assertTrue(result)
        self.assertIn(0, self.manager.active_widgets)
        self.assertEqual(self.manager.active_widgets[0]["button_config"], button_config)

    def test_setup_widget_button_no_widget_config(self):
        """Test setup fails when no widget config."""
        button_config = {"text": "No widget"}
        
        result = self.manager.setup_widget_button(0, button_config, {})
        
        self.assertFalse(result)
        self.assertNotIn(0, self.manager.active_widgets)

    def test_setup_widget_button_missing_type(self):
        """Test setup fails when widget type missing."""
        button_config = {"widget": {}}
        
        result = self.manager.setup_widget_button(0, button_config, {})
        
        self.assertFalse(result)

    def test_setup_widget_button_unknown_type(self):
        """Test setup fails for unknown widget type."""
        button_config = {"widget": {"type": "unknown"}}
        
        result = self.manager.setup_widget_button(0, button_config, {})
        
        self.assertFalse(result)

    def test_render_widget(self):
        """Test rendering a widget."""
        button_config = {
            "widget": {"type": "mock"},
            "text": "Original"
        }
        self.manager.setup_widget_button(0, button_config, {})
        
        # Mock rendered image
        self.button_renderer.render_button.return_value = b"test_image_data"
        
        result = self.manager.render_widget(0, {}, self.deck, force=True)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, b"test_image_data")
        self.assertTrue(self.manager.active_widgets[0]["widget"].fetch_called)
        self.assertTrue(self.manager.active_widgets[0]["widget"].render_called)

    def test_render_widget_nonexistent(self):
        """Test rendering a nonexistent widget."""
        result = self.manager.render_widget(99, {}, self.deck)
        self.assertIsNone(result)

    def test_update_widgets(self):
        """Test updating widgets that need refresh."""
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        # Force widget to need update
        widget_data = self.manager.active_widgets[0]
        widget_data["widget"]._last_update = 0.0
        
        self.button_renderer.render_button.return_value = b"updated_image"
        
        updates = self.manager.update_widgets(self.deck, {})
        
        self.assertIn(0, updates)
        self.assertEqual(updates[0], b"updated_image")

    def test_update_widgets_no_update_needed(self):
        """Test that widgets don't update when not needed."""
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        # Set recent update time
        widget_data = self.manager.active_widgets[0]
        widget_data["widget"]._last_update = time.time()
        
        updates = self.manager.update_widgets(self.deck, {})
        
        # Should return empty dict (no updates needed)
        self.assertEqual(len(updates), 0)

    def test_clear_widgets(self):
        """Test clearing all widgets."""
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        self.assertEqual(len(self.manager.active_widgets), 1)
        
        self.manager.clear_widgets()
        
        self.assertEqual(len(self.manager.active_widgets), 0)
        self.assertEqual(self.manager._total_cache_size, 0)

    def test_has_widgets(self):
        """Test checking if widgets are active."""
        self.assertFalse(self.manager.has_widgets())
        
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        self.assertTrue(self.manager.has_widgets())

    def test_get_widget_count(self):
        """Test getting widget count."""
        self.assertEqual(self.manager.get_widget_count(), 0)
        
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        self.assertEqual(self.manager.get_widget_count(), 1)

    def test_cache_size_tracking(self):
        """Test that cache size is tracked correctly."""
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        # Mock rendered image
        test_image = b"x" * 1000  # 1KB image
        self.button_renderer.render_button.return_value = test_image
        
        self.manager.render_widget(0, {}, self.deck, force=True)
        
        self.assertEqual(self.manager.get_cache_size(), 1000)

    def test_cache_eviction(self):
        """Test cache eviction when limit exceeded."""
        # Set low cache limit for testing
        original_limit = self.manager.MAX_TOTAL_CACHE_SIZE
        self.manager.MAX_TOTAL_CACHE_SIZE = 2000  # 2KB limit
        
        try:
            # Create multiple widgets with large caches
            for i in range(3):
                button_config = {"widget": {"type": "mock"}}
                self.manager.setup_widget_button(i, button_config, {})
                
                test_image = b"x" * 1000  # 1KB each
                self.button_renderer.render_button.return_value = test_image
                self.manager.render_widget(i, {}, self.deck, force=True)
                time.sleep(0.01)  # Ensure different timestamps
            
            # Cache should have been evicted
            self.assertLessEqual(self.manager.get_cache_size(), 2000)
            
        finally:
            self.manager.MAX_TOTAL_CACHE_SIZE = original_limit

    def test_thread_safety(self):
        """Test that widget operations are thread-safe."""
        import threading
        
        button_config = {"widget": {"type": "mock"}}
        self.manager.setup_widget_button(0, button_config, {})
        
        def update_worker():
            self.button_renderer.render_button.return_value = b"test"
            self.manager.update_widgets(self.deck, {})
        
        # Run multiple threads
        threads = [threading.Thread(target=update_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should not crash - basic thread safety test


if __name__ == "__main__":
    unittest.main()

