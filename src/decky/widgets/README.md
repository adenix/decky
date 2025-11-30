# Decky Widgets

Widgets are auto-updating Stream Deck buttons that display dynamic content.

## Overview

Unlike regular buttons that show static content until clicked, widgets automatically refresh their display based on configured update intervals. This enables real-time dashboards showing time, weather, system stats, and more.

## Architecture

```
BaseWidget (Abstract)
├── ClockWidget - Display current time
├── DateWidget - Display current date
├── CPUWidget - CPU usage percentage
├── MemoryWidget - RAM usage
├── DiskWidget - Disk usage
├── NetworkWidget - Network speeds
└── WeatherWidget - Weather from API
```

## Creating Custom Widgets

### 1. Basic Widget

```python
from decky.widgets.base import BaseWidget

class MyWidget(BaseWidget):
    widget_type = "my_widget"  # Unique identifier
    update_interval = 5.0  # Update every 5 seconds
    
    def fetch_data(self):
        """Fetch fresh data"""
        return {"value": 42}
    
    def render_text(self, data):
        """Format data as text"""
        return f"Value\n{data['value']}"
```

### 2. Widget with Validation

```python
class APIWidget(BaseWidget):
    widget_type = "api_widget"
    update_interval = 60.0
    
    def validate_config(self):
        """Validate required parameters"""
        if not self.config.get("api_key"):
            logger.error("Widget requires 'api_key'")
            return False
        return True
    
    def fetch_data(self):
        # Fetch from API
        pass
    
    def render_text(self, data):
        return str(data)
    
    def get_required_params(self):
        return ["api_key"]
```

### 3. Widget with Dynamic Icon

```python
from PIL import Image, ImageDraw

class GaugeWidget(BaseWidget):
    widget_type = "gauge"
    update_interval = 2.0
    
    def fetch_data(self):
        return {"percent": 75}
    
    def render_text(self, data):
        return f"{data['percent']:.0f}%"
    
    def render_icon(self, data):
        """Render a gauge icon"""
        img = Image.new('RGB', (72, 72), 'black')
        draw = ImageDraw.Draw(img)
        
        # Draw arc based on percentage
        angle = int(data['percent'] * 3.6)
        draw.arc([(10, 10), (62, 62)], 0, angle, fill='green', width=5)
        
        return img
```

## Widget Lifecycle

1. **Initialization**: Widget created when page loads
2. **Validation**: `validate_config()` checks parameters
3. **First Render**: `fetch_data()` + `render_text()` called
4. **Update Loop**: Based on `update_interval`:
   - Check if update needed (`should_update()`)
   - Fetch fresh data
   - Render new image
   - Update button
5. **Cleanup**: Widget cleared on page switch

## Update Intervals

Different widgets update at different rates:

| Widget | Interval | Reason |
|--------|----------|---------|
| Clock | 1s | Needs second precision |
| Date | 60s | Only changes daily |
| CPU | 2s | Balance freshness/load |
| Memory | 5s | Changes moderately |
| Disk | 30s | Changes slowly |
| Weather | 600s | API rate limits |
| Network | 2s | Real-time monitoring |

## Error Handling

Widgets should handle errors gracefully:

```python
def fetch_data(self):
    try:
        # Fetch data
        result = api_call()
        return result
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        # Return cached data or fallback
        return self._cached_data or {"value": "N/A"}
```

## Configuration

### Basic Widget

```yaml
buttons:
  1:
    widget:
      type: clock
      format: "%H:%M:%S"
```

### Widget with Parameters

```yaml
buttons:
  1:
    widget:
      type: weather
      location: "San Francisco, CA"
      api_key: "${OPENWEATHER_API_KEY}"
      unit: fahrenheit
      format: detailed
```

### Widget with Action

```yaml
buttons:
  1:
    widget:
      type: cpu
    action:
      type: command
      command: gnome-system-monitor
```

## Best Practices

1. **Keep `fetch_data()` Fast**: Use caching, async operations
2. **Handle Errors**: Always return fallback data
3. **Respect API Limits**: Use appropriate intervals
4. **Cache Results**: Store `_cached_data` for error cases
5. **Validate Config**: Check required parameters in `validate_config()`
6. **Log Errors**: Help users debug configuration issues

## Testing

```python
def test_my_widget():
    widget = MyWidget({"param": "value"})
    
    # Test data fetching
    data = widget.fetch_data()
    assert data is not None
    
    # Test rendering
    text = widget.render_text(data)
    assert len(text) > 0
    
    # Test update interval
    assert widget.should_update(time.time())
```

## Environment Variables

Use environment variables for sensitive data:

```yaml
widget:
  type: weather
  api_key: "${OPENWEATHER_API_KEY}"  # Expands at runtime
```

## Performance Considerations

- **Memory**: Each widget instance uses ~1-5KB
- **CPU**: Minimal (<0.1% per widget)
- **Network**: Only API-based widgets (weather, etc.)
- **Caching**: Rendered images cached between updates

## Available Widgets

### DateTime (`datetime`) ⭐ Recommended
- Display date and/or time with any format
- Parameters: 
  - `format` (required): strftime format string
  - `update_interval` (optional): Update frequency in seconds (auto-detected if not set)
- Auto-detects optimal update interval:
  - Formats with `%S` (seconds) → 1 second
  - Formats with time but no seconds → 10 seconds
  - Date-only formats → 60 seconds
- Examples:
  ```yaml
  # Time with seconds
  widget:
    type: datetime
    format: "%H:%M:%S"
  
  # 12-hour clock
  widget:
    type: datetime
    format: "%I:%M %p"
  
  # Day and date
  widget:
    type: datetime
    format: "%a\n%b %d"
  
  # Full datetime
  widget:
    type: datetime
    format: "%a %b %d\n%I:%M %p"
  
  # Custom interval
  widget:
    type: datetime
    format: "%H:%M:%S"
    update_interval: 0.5  # Update twice per second
  ```


### CPU (`cpu`)
- CPU usage percentage
- Parameters: `icon`, `interval`
- Requires: `psutil`

### Memory (`memory`)
- RAM usage
- Parameters: `show_details`, `icon`
- Requires: `psutil`

### Disk (`disk`)
- Disk usage
- Parameters: `path`, `show_free`, `icon`
- Requires: `psutil`

### Network (`network`)
- Upload/download speed
- Parameters: `icon`
- Requires: `psutil`

### Weather (`weather`)
- Weather from OpenWeatherMap
- Parameters: `location`, `api_key`, `unit`, `format`
- Update: Every 10 minutes

## Troubleshooting

**Widget not updating?**
- Check logs for errors
- Verify update_interval is set
- Ensure fetch_data() doesn't raise exceptions

**"Widget requires XYZ"?**
- Missing required parameter
- Check validate_config() requirements

**High CPU usage?**
- Reduce update frequency
- Optimize fetch_data() method
- Check for infinite loops

**API errors?**
- Verify API key is correct
- Check network connectivity
- Respect rate limits

## Future Enhancements

Potential widget types:
- Email/notification count
- Stock prices
- Spotify now playing
- Docker container status
- GitHub notifications
- Todo list integration
- Calendar events
- Cryptocurrency prices
- Battery status

