"""
Tests for individual widget implementations.
"""

import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from decky.widgets.clock import DateTimeWidget


class TestDateTimeWidget(unittest.TestCase):
    """Test DateTimeWidget functionality."""

    def test_widget_type(self):
        """Test widget type is set correctly."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        self.assertEqual(widget.widget_type, "datetime")

    def test_auto_interval_seconds(self):
        """Test auto-detection of 1s interval for formats with seconds."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        self.assertEqual(widget.update_interval, 1.0)

    def test_auto_interval_minutes(self):
        """Test auto-detection of 10s interval for formats with minutes."""
        widget = DateTimeWidget({"format": "%H:%M"})
        self.assertEqual(widget.update_interval, 10.0)

    def test_auto_interval_12hour(self):
        """Test auto-detection for 12-hour format."""
        widget = DateTimeWidget({"format": "%I:%M %p"})
        self.assertEqual(widget.update_interval, 10.0)

    def test_auto_interval_date_only(self):
        """Test auto-detection of 60s interval for date-only formats."""
        widget = DateTimeWidget({"format": "%a\n%b %d"})
        self.assertEqual(widget.update_interval, 60.0)

    def test_manual_interval_override(self):
        """Test manual override of update interval."""
        widget = DateTimeWidget({"format": "%H:%M:%S", "update_interval": 0.5})
        self.assertEqual(widget.update_interval, 0.5)

    def test_fetch_data(self):
        """Test fetching current datetime."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        result = widget.fetch_data()
        self.assertIsInstance(result, datetime)

    def test_render_time(self):
        """Test rendering time format."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        test_time = datetime(2024, 1, 15, 14, 30, 45)
        result = widget.render_text(test_time)
        self.assertEqual(result, "14:30:45")

    def test_render_date(self):
        """Test rendering date format."""
        widget = DateTimeWidget({"format": "%Y-%m-%d"})
        test_date = datetime(2024, 1, 15, 14, 30, 45)
        result = widget.render_text(test_date)
        self.assertEqual(result, "2024-01-15")

    def test_render_multiline(self):
        """Test rendering multiline format."""
        widget = DateTimeWidget({"format": "%a\n%b %d"})
        test_date = datetime(2024, 1, 15, 14, 30, 45)  # Monday
        result = widget.render_text(test_date)
        self.assertIn("Mon", result)
        self.assertIn("Jan 15", result)

    def test_render_none_data(self):
        """Test rendering with None data."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        result = widget.render_text(None)
        self.assertEqual(result, "---")

    def test_get_fallback_data(self):
        """Test fallback data returns valid datetime."""
        widget = DateTimeWidget({"format": "%H:%M:%S"})
        result = widget.get_fallback_data()
        self.assertIsInstance(result, datetime)




class TestSystemWidgets(unittest.TestCase):
    """Test system monitoring widgets."""

    def test_cpu_widget_type(self):
        """Test CPU widget type."""
        try:
            from decky.widgets.system import CPUWidget
            widget = CPUWidget({})
            self.assertEqual(widget.widget_type, "cpu")
            self.assertEqual(widget.update_interval, 2.0)
        except ImportError:
            self.skipTest("psutil not available")

    def test_cpu_widget_render_none(self):
        """Test CPU widget renders None data gracefully."""
        try:
            from decky.widgets.system import CPUWidget
            widget = CPUWidget({})
            result = widget.render_text(None)
            self.assertIn("CPU", result)
            self.assertIn("N/A", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_cpu_widget_render_normal(self):
        """Test CPU widget renders normal data."""
        try:
            from decky.widgets.system import CPUWidget
            widget = CPUWidget({})
            result = widget.render_text(45.7)
            self.assertIn("CPU", result)
            self.assertIn("45.7%", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_cpu_widget_fallback_data(self):
        """Test CPU widget fallback data."""
        try:
            from decky.widgets.system import CPUWidget
            widget = CPUWidget({})
            result = widget.get_fallback_data()
            self.assertEqual(result, 0.0)
        except ImportError:
            self.skipTest("psutil not available")

    def test_memory_widget_type(self):
        """Test Memory widget type."""
        try:
            from decky.widgets.system import MemoryWidget
            widget = MemoryWidget({})
            self.assertEqual(widget.widget_type, "memory")
            self.assertEqual(widget.update_interval, 5.0)
        except ImportError:
            self.skipTest("psutil not available")

    def test_memory_widget_render_percent(self):
        """Test Memory widget renders percentage."""
        try:
            from decky.widgets.system import MemoryWidget
            widget = MemoryWidget({})
            data = {"percent": 65.5, "used_gb": 8.2, "total_gb": 16.0}
            result = widget.render_text(data)
            self.assertIn("RAM", result)
            self.assertIn("65.5%", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_memory_widget_render_details(self):
        """Test Memory widget renders details."""
        try:
            from decky.widgets.system import MemoryWidget
            widget = MemoryWidget({"show_details": True})
            data = {"percent": 65.5, "used_gb": 8.2, "total_gb": 16.0}
            result = widget.render_text(data)
            self.assertIn("RAM", result)
            self.assertIn("8.2", result)
            self.assertIn("16.0", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_disk_widget_type(self):
        """Test Disk widget type."""
        try:
            from decky.widgets.system import DiskWidget
            widget = DiskWidget({})
            self.assertEqual(widget.widget_type, "disk")
            self.assertEqual(widget.update_interval, 30.0)
        except ImportError:
            self.skipTest("psutil not available")

    def test_network_widget_type(self):
        """Test Network widget type."""
        try:
            from decky.widgets.system import NetworkWidget
            widget = NetworkWidget({})
            self.assertEqual(widget.widget_type, "network")
            self.assertEqual(widget.update_interval, 2.0)
        except ImportError:
            self.skipTest("psutil not available")

    def test_network_widget_render(self):
        """Test Network widget renders speeds."""
        try:
            from decky.widgets.system import NetworkWidget
            widget = NetworkWidget({})
            data = {"upload_kbps": 125.5, "download_kbps": 512.3}
            result = widget.render_text(data)
            self.assertIn("↓", result)
            self.assertIn("↑", result)
            self.assertIn("512KB/s", result)
            self.assertIn("125KB/s", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_network_widget_render_mb(self):
        """Test Network widget renders MB/s."""
        try:
            from decky.widgets.system import NetworkWidget
            widget = NetworkWidget({})
            data = {"upload_kbps": 2048.0, "download_kbps": 5120.0}
            result = widget.render_text(data)
            self.assertIn("MB/s", result)
        except ImportError:
            self.skipTest("psutil not available")

    def test_network_widget_thread_safety(self):
        """Test Network widget has thread safety."""
        try:
            from decky.widgets.system import NetworkWidget
            widget = NetworkWidget({})
            self.assertTrue(hasattr(widget, "_lock"))
        except ImportError:
            self.skipTest("psutil not available")


class TestBaseWidget(unittest.TestCase):
    """Test BaseWidget base class functionality."""

    def test_safe_fetch_data_success(self):
        """Test safe_fetch_data on success."""
        from decky.widgets.base import BaseWidget
        
        class TestWidget(BaseWidget):
            widget_type = "test"
            
            def fetch_data(self):
                return "success"
            
            def render_text(self, data):
                return data
        
        widget = TestWidget({})
        result = widget.safe_fetch_data()
        self.assertEqual(result, "success")
        self.assertEqual(widget._cached_data, "success")

    def test_safe_fetch_data_error_with_cache(self):
        """Test safe_fetch_data returns cache on error."""
        from decky.widgets.base import BaseWidget
        
        class TestWidget(BaseWidget):
            widget_type = "test"
            
            def fetch_data(self):
                raise Exception("Test error")
            
            def render_text(self, data):
                return str(data)
            
            def get_fallback_data(self):
                return "fallback"
        
        widget = TestWidget({})
        widget._cached_data = "cached"
        result = widget.safe_fetch_data()
        self.assertEqual(result, "cached")

    def test_safe_fetch_data_error_no_cache(self):
        """Test safe_fetch_data returns fallback when no cache."""
        from decky.widgets.base import BaseWidget
        
        class TestWidget(BaseWidget):
            widget_type = "test"
            
            def fetch_data(self):
                raise Exception("Test error")
            
            def render_text(self, data):
                return str(data)
            
            def get_fallback_data(self):
                return "fallback"
        
        widget = TestWidget({})
        result = widget.safe_fetch_data()
        self.assertEqual(result, "fallback")


if __name__ == "__main__":
    unittest.main()

