"""
Button rendering for Stream Deck
"""

import logging
import os
from typing import Any, Dict, Optional

from PIL import Image, ImageDraw, ImageFont
from PIL.Image import UnidentifiedImageError
from StreamDeck.ImageHelpers import PILHelper

logger = logging.getLogger(__name__)


class ButtonRenderer:
    """
    Renders button images for Stream Deck devices.

    This class handles all aspects of button image generation including:
    - Text rendering with custom fonts and styles
    - Icon loading and scaling
    - Transparency handling
    - Multi-line text support
    - Text shadows for readability over icons

    The renderer caches fonts for performance and supports various
    image formats through PIL/Pillow.

    Attributes:
        font_cache: Dictionary mapping font keys to loaded ImageFont objects
    """

    def __init__(self):
        """Initialize the button renderer with an empty font cache."""
        self.font_cache = {}

    def render_button(self, button_config: Dict[str, Any], styles: Dict[str, Any], deck) -> bytes:
        """Render a button image"""
        # Get button style
        style_name = button_config.get("style", "default")
        style = styles.get(style_name, styles.get("default", {}))

        # Get image dimensions
        image_size = deck.key_image_format()["size"]

        # Create base image
        bg_color = style.get("background_color", "#000000")
        image = Image.new("RGB", image_size, bg_color)
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
                    if icon.mode == "RGBA":
                        temp = Image.new("RGB", icon.size, bg_color)
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
                    icon_pos = (
                        (image_size[0] - icon.width) // 2,
                        (image_size[1] - icon.height) // 2,
                    )
                    image.paste(icon, icon_pos)
                    icon_loaded = True

                except (FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Cannot access icon file {icon_file}: {e}")
                except UnidentifiedImageError as e:
                    logger.warning(f"Invalid or corrupted image file {icon_file}: {e}")
                except OSError as e:
                    logger.warning(f"Error reading icon file {icon_file}: {e}")
                except Exception as e:
                    # Unexpected errors should be logged with full traceback
                    logger.error(f"Unexpected error loading icon {icon_file}: {e}", exc_info=True)

        # Draw text
        text = button_config.get("text") or button_config.get("label", "")
        if text:
            self._draw_text(draw, text, style, image_size, icon_loaded)

        return PILHelper.to_native_format(deck, image)

    def render_button_with_icon(
        self, button_config: Dict[str, Any], styles: Dict[str, Any], deck, icon_image: Image.Image
    ) -> bytes:
        """Render a button with a pre-loaded icon image (for animated frames)"""
        # Get button style
        style_name = button_config.get("style", "default")
        style = styles.get(style_name, styles.get("default", {}))

        # Get image dimensions
        image_size = deck.key_image_format()["size"]

        # Create base image
        bg_color = style.get("background_color", "#000000")
        image = Image.new("RGB", image_size, bg_color)
        draw = ImageDraw.Draw(image)

        # Process the provided icon image
        icon_loaded = False
        if icon_image:
            try:
                icon = icon_image.copy()

                # Handle transparency
                if icon.mode == "RGBA":
                    temp = Image.new("RGB", icon.size, bg_color)
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
                icon_pos = (
                    (image_size[0] - icon.width) // 2,
                    (image_size[1] - icon.height) // 2,
                )
                image.paste(icon, icon_pos)
                icon_loaded = True

            except OSError as e:
                logger.warning(f"Error processing icon frame: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing icon frame: {e}", exc_info=True)

        # Draw text
        text = button_config.get("text") or button_config.get("label", "")
        if text:
            self._draw_text(draw, text, style, image_size, icon_loaded)

        return PILHelper.to_native_format(deck, image)

    def render_blank(self, deck) -> bytes:
        """Render a blank button"""
        image_size = deck.key_image_format()["size"]
        image = Image.new("RGB", image_size, "black")
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
            os.getcwd(),
        ]

        for base_path in search_paths:
            full_path = os.path.join(base_path, icon_path)
            if os.path.exists(full_path):
                return full_path

        return None

    def _draw_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        style: Dict[str, Any],
        image_size: tuple,
        icon_loaded: bool,
    ) -> None:
        """
        Draw text on a Stream Deck button image.

        Renders multi-line text with configurable styling including font, color,
        alignment, and optional border/shadow for improved readability.

        Args:
            draw: PIL ImageDraw object to draw on
            text: Text to render. Use '\\n' for multi-line text
            style: Style dictionary containing:
                - font (str): Font name or path
                - font_size (int): Size in points
                - text_color (str): Hex color code (e.g., '#FFFFFF')
                - text_align (str): 'top', 'center', or 'bottom'
                - text_offset (int): Fine-tune vertical position in pixels
                - border_size (int): Border thickness in pixels (default: 1 if icon_loaded, else 0)
                - border_color (str): Border color hex code (default: '#000000')
            image_size: Button dimensions as (width, height) tuple in pixels
            icon_loaded: If True, border_size defaults to 1 (can still be overridden)

        Note:
            Text is automatically centered horizontally. Vertical alignment
            is controlled by style['text_align']. The border/shadow helps ensure
            text is readable over icons or busy backgrounds.

        Example:
            >>> style = {
            ...     "font": "DejaVu Sans",
            ...     "font_size": 14,
            ...     "text_color": "#FFFFFF",
            ...     "text_align": "bottom",
            ...     "text_offset": 0,
            ...     "border_size": 2,
            ...     "border_color": "#000000"
            ... }
            >>> self._draw_text(draw, "Hello\\nWorld", style, (72, 72), False)
        """
        font_name = style.get("font", "DejaVu Sans")
        font_size = style.get("font_size", 14)
        text_color = style.get("text_color", "#FFFFFF")
        text_align = style.get("text_align", "bottom")
        text_offset = style.get("text_offset", 0)
        
        # Text border/shadow (useful for text over icons)
        border_size = style.get("border_size", 1 if icon_loaded else 0)
        border_color = style.get("border_color", "#000000")

        # Load font
        font = self._load_font(font_name, font_size)

        # Process multi-line text
        lines = text.split("\n")
        
        # Calculate actual text height using font metrics
        # We need to get bboxes for all lines to calculate total visual height
        line_bboxes = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_bboxes.append(bbox)
        
        # Calculate total height of text block
        # For multi-line text, we need to stack them vertically
        line_spacing = 2
        if len(lines) == 1:
            # Single line: just use the bbox height
            total_text_height = line_bboxes[0][3] - line_bboxes[0][1]
        else:
            # Multi-line: sum heights and add spacing
            total_text_height = sum(bbox[3] - bbox[1] for bbox in line_bboxes)
            total_text_height += (len(lines) - 1) * line_spacing

        # Calculate vertical starting position for the text block
        if text_align == "top":
            y_start = 8
        elif text_align == "center":
            # Center the entire text block vertically
            y_start = (image_size[1] - total_text_height) // 2
        else:  # bottom
            y_start = image_size[1] - total_text_height - 8

        # Apply fine adjustment
        y_start += text_offset

        # Draw each line
        y_offset = y_start
        for i, line in enumerate(lines):
            bbox = line_bboxes[i]
            
            # Calculate horizontal center position
            line_width = bbox[2] - bbox[0]
            text_x = (image_size[0] - line_width) // 2

            # Account for bbox top offset to position text correctly
            # The bbox[1] (top) can be negative for tall ascenders
            line_y = y_offset - bbox[1]

            # Draw text border/shadow if enabled
            if border_size and border_size > 0:
                # Create border by drawing text in multiple positions around the main position
                for dx in range(-border_size, border_size + 1):
                    for dy in range(-border_size, border_size + 1):
                        if dx != 0 or dy != 0:
                            draw.text(
                                (text_x + dx, line_y + dy), 
                                line, 
                                font=font, 
                                fill=border_color
                            )

            # Draw the actual text
            draw.text((text_x, line_y), line, font=font, fill=text_color)
            
            # Move to next line using actual line height
            y_offset += (bbox[3] - bbox[1]) + line_spacing

    def _load_font(self, font_name: str, font_size: int):
        """Load a font with caching"""
        cache_key = f"{font_name}_{font_size}"

        if cache_key in self.font_cache:
            return self.font_cache[cache_key]

        font = None

        # Try to load the specified font
        if "/" in font_name or font_name.endswith(".ttf"):
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
                os.path.expanduser("~/.local/share/fonts"),
            ]

            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue

                for root, _dirs, files in os.walk(font_dir):
                    for file in files:
                        if file.endswith((".ttf", ".otf")):
                            if font_name.lower().replace(" ", "") in file.lower().replace(" ", ""):
                                font_path = os.path.join(root, file)
                                try:
                                    font = ImageFont.truetype(font_path, font_size)
                                    logger.debug(f"Loaded font: {font_path}")
                                    break
                                except OSError as e:
                                    # Font file might be corrupted or inaccessible
                                    logger.debug(f"Cannot load font {font_path}: {e}")
                                    continue
                                except Exception as e:
                                    # Unexpected error, log but continue searching
                                    logger.warning(
                                        f"Unexpected error loading font {font_path}: {e}"
                                    )
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
