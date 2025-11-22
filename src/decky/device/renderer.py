"""
Button rendering for Stream Deck
"""

import os
import logging
from typing import Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper

logger = logging.getLogger(__name__)


class ButtonRenderer:
    """Renders button images for Stream Deck"""

    def __init__(self):
        self.font_cache = {}

    def render_button(self, button_config: Dict[str, Any], styles: Dict[str, Any], deck) -> bytes:
        """Render a button image"""
        # Get button style
        style_name = button_config.get("style", "default")
        style = styles.get(style_name, styles.get("default", {}))

        # Get image dimensions
        image_size = deck.key_image_format()['size']

        # Create base image
        bg_color = style.get("background_color", "#000000")
        image = Image.new('RGB', image_size, bg_color)
        draw = ImageDraw.Draw(image)

        # Check for icon
        icon_path = button_config.get("icon")
        icon_loaded = False

        if icon_path:
            icon_file = self._find_icon(icon_path)
            if icon_file and os.path.exists(icon_file):
                try:
                    icon = Image.open(icon_file)

                    # Handle transparency
                    if icon.mode == 'RGBA':
                        temp = Image.new('RGB', icon.size, bg_color)
                        temp.paste(icon, (0, 0), icon)
                        icon = temp

                    # Scale to fill button
                    scale_w = image_size[0] / icon.width
                    scale_h = image_size[1] / icon.height
                    scale = max(scale_w, scale_h)

                    new_size = (int(icon.width * scale), int(icon.height * scale))
                    icon = icon.resize(new_size, Image.Resampling.LANCZOS)

                    # Crop if needed
                    if icon.width > image_size[0] or icon.height > image_size[1]:
                        left = (icon.width - image_size[0]) // 2
                        top = (icon.height - image_size[1]) // 2
                        right = left + image_size[0]
                        bottom = top + image_size[1]
                        icon = icon.crop((left, top, right, bottom))

                    # Paste icon
                    icon_pos = ((image_size[0] - icon.width) // 2,
                               (image_size[1] - icon.height) // 2)
                    image.paste(icon, icon_pos)
                    icon_loaded = True

                except Exception as e:
                    logger.warning(f"Failed to load icon {icon_file}: {e}")

        # Draw text
        text = button_config.get("text") or button_config.get("label", "")
        if text:
            self._draw_text(draw, text, style, image_size, icon_loaded)

        return PILHelper.to_native_format(deck, image)

    def render_button_with_icon(self, button_config: Dict[str, Any], styles: Dict[str, Any], deck, icon_image: Image.Image) -> bytes:
        """Render a button with a pre-loaded icon image (for animated frames)"""
        # Get button style
        style_name = button_config.get("style", "default")
        style = styles.get(style_name, styles.get("default", {}))

        # Get image dimensions
        image_size = deck.key_image_format()['size']

        # Create base image
        bg_color = style.get("background_color", "#000000")
        image = Image.new('RGB', image_size, bg_color)
        draw = ImageDraw.Draw(image)

        # Process the provided icon image
        icon_loaded = False
        if icon_image:
            try:
                icon = icon_image.copy()

                # Handle transparency
                if icon.mode == 'RGBA':
                    temp = Image.new('RGB', icon.size, bg_color)
                    temp.paste(icon, (0, 0), icon)
                    icon = temp

                # Scale to fill button
                scale_w = image_size[0] / icon.width
                scale_h = image_size[1] / icon.height
                scale = max(scale_w, scale_h)

                new_size = (int(icon.width * scale), int(icon.height * scale))
                icon = icon.resize(new_size, Image.Resampling.LANCZOS)

                # Crop if needed
                if icon.width > image_size[0] or icon.height > image_size[1]:
                    left = (icon.width - image_size[0]) // 2
                    top = (icon.height - image_size[1]) // 2
                    right = left + image_size[0]
                    bottom = top + image_size[1]
                    icon = icon.crop((left, top, right, bottom))

                # Paste icon
                icon_pos = ((image_size[0] - icon.width) // 2,
                           (image_size[1] - icon.height) // 2)
                image.paste(icon, icon_pos)
                icon_loaded = True

            except Exception as e:
                logger.warning(f"Failed to process icon frame: {e}")

        # Draw text
        text = button_config.get("text") or button_config.get("label", "")
        if text:
            self._draw_text(draw, text, style, image_size, icon_loaded)

        return PILHelper.to_native_format(deck, image)

    def render_blank(self, deck) -> bytes:
        """Render a blank button"""
        image_size = deck.key_image_format()['size']
        image = Image.new('RGB', image_size, 'black')
        return PILHelper.to_native_format(deck, image)

    def _find_icon(self, icon_path: str) -> Optional[str]:
        """Find icon file by name or path"""
        # Expand user path
        icon_path = os.path.expanduser(icon_path)

        # If absolute path, return as-is
        if os.path.isabs(icon_path):
            return icon_path if os.path.exists(icon_path) else None

        # Search relative paths
        search_paths = [
            os.path.expanduser("~/.decky"),
            os.path.expanduser("~/.decky/icons"),
            os.getcwd()
        ]

        for base_path in search_paths:
            full_path = os.path.join(base_path, icon_path)
            if os.path.exists(full_path):
                return full_path

        return None

    def _draw_text(self, draw, text: str, style: Dict[str, Any], image_size: tuple, icon_loaded: bool):
        """Draw text on button"""
        font_name = style.get("font", "DejaVu Sans")
        font_size = style.get("font_size", 14)
        text_color = style.get("text_color", "#FFFFFF")
        text_align = style.get("text_align", "bottom")
        text_offset = style.get("text_offset", 0)

        # Load font
        font = self._load_font(font_name, font_size)

        # Process multi-line text
        lines = text.split('\n')
        total_text_height = len(lines) * (font_size + 2)

        # Calculate vertical position
        if text_align == "top":
            y_offset = 8
        elif text_align == "center":
            y_offset = (image_size[1] - total_text_height) // 2
        else:  # bottom
            y_offset = image_size[1] - total_text_height - 8

        # Apply fine adjustment
        y_offset += text_offset

        # Draw each line
        for line in lines:
            # Get text dimensions
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            text_x = (image_size[0] - line_width) // 2

            if icon_loaded:
                # Add shadow for readability over icons
                shadow_color = "#000000"
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx != 0 or dy != 0:
                            draw.text((text_x + dx, y_offset + dy), line,
                                    font=font, fill=shadow_color)

            # Draw the actual text
            draw.text((text_x, y_offset), line, font=font, fill=text_color)
            y_offset += font_size + 2

    def _load_font(self, font_name: str, font_size: int):
        """Load a font with caching"""
        cache_key = f"{font_name}_{font_size}"

        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        font = None

        # Try to load the specified font
        if '/' in font_name or font_name.endswith('.ttf'):
            # It's a path
            font_path = os.path.expanduser(font_name)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                logger.warning(f"Failed to load font from path '{font_path}': {e}")

        if not font:
            # Search for font in system directories
            font_dirs = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts")
            ]

            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue

                for root, dirs, files in os.walk(font_dir):
                    for file in files:
                        if file.endswith(('.ttf', '.otf')):
                            if font_name.lower().replace(' ', '') in file.lower().replace(' ', ''):
                                font_path = os.path.join(root, file)
                                try:
                                    font = ImageFont.truetype(font_path, font_size)
                                    logger.debug(f"Loaded font: {font_path}")
                                    break
                                except Exception:
                                    continue
                    if font:
                        break
                if font:
                    break

        # Fallback to default
        if not font:
            logger.warning(f"Failed to load font '{font_name}', using default")
            font = ImageFont.load_default()

        self.font_cache[cache_key] = font
        return font