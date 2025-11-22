#!/usr/bin/env python3
"""
Decky - A simple YAML-driven Stream Deck controller for Linux
"""

import sys
import os
import yaml
import subprocess
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Stream Deck library
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

logger = logging.getLogger(__name__)


class DeckyController:
    """Main controller for Stream Deck with YAML configuration"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_page = "main"
        self.deck = None
        self.button_states = {}
        self.styles = self.config.get("styles", {})
        self.pages = self.config.get("pages", {})
        self.animated_buttons = {}  # Store animated GIF data: {key: {'frames': [...], 'current': 0, 'durations': []}}
        self.animation_counter = 0

    def _load_config(self) -> Dict:
        """Load YAML configuration file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def reload_config(self):
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        self.config = self._load_config()
        self.styles = self.config.get("styles", {})
        self.pages = self.config.get("pages", {})
        if self.deck:
            self._update_page()

    def connect(self) -> bool:
        """Connect to Stream Deck device"""
        decks = DeviceManager().enumerate()

        if not decks:
            logger.error("No Stream Deck devices found")
            return False

        self.deck = decks[0]
        self.deck.open()
        self.deck.reset()

        # Set brightness
        brightness = self.config.get("device", {}).get("brightness", 75)
        self.deck.set_brightness(brightness)

        # Set up key callback
        self.deck.set_key_callback(self._key_change_callback)

        logger.info(f"Connected to {self.deck.deck_type()} with {self.deck.key_count()} keys")
        return True

    def _setup_animated_button(self, key_index: int, button_config: Dict, icon_file: str):
        """Set up animated GIF frames for a button"""
        try:
            gif = Image.open(icon_file)
            if hasattr(gif, 'is_animated') and gif.is_animated:
                frames = []
                durations = []

                for frame_num in range(gif.n_frames):
                    gif.seek(frame_num)
                    frame = gif.copy()
                    frames.append(frame)
                    durations.append(gif.info.get('duration', 100))

                if frames:
                    self.animated_buttons[key_index] = {
                        'frames': frames,
                        'durations': durations,
                        'current_frame': 0,
                        'last_update': time.time(),
                        'config': button_config
                    }
                    logger.info(f"Loaded {len(frames)} frames for animated button {key_index+1}")
        except Exception as e:
            logger.warning(f"Failed to load animated GIF {icon_file}: {e}")

    def _update_animations(self):
        """Update animated buttons"""
        current_time = time.time()

        for key_index, anim_data in self.animated_buttons.items():
            # Check if it's time to advance to next frame
            frame_duration = anim_data['durations'][anim_data['current_frame']] / 1000.0  # Convert ms to seconds
            if current_time - anim_data['last_update'] >= frame_duration:
                # Advance to next frame
                anim_data['current_frame'] = (anim_data['current_frame'] + 1) % len(anim_data['frames'])
                anim_data['last_update'] = current_time

                # Update button image with new frame
                image = self._create_button_image(anim_data['config'], key_index)
                self.deck.set_key_image(key_index, image)

    def _create_button_image(self, button_config: Dict, key_index: int = None) -> Image:
        """Create button image from configuration"""
        # Get button dimensions
        image_size = self.deck.key_image_format()['size']

        # Create base image
        style_name = button_config.get("style", "default")
        style = self.styles.get(style_name, {})

        bg_color = style.get("background_color", "#333333")
        image = Image.new("RGB", image_size, color=bg_color)
        draw = ImageDraw.Draw(image)

        # Load icon if specified
        icon_path = button_config.get("icon")
        icon_loaded = False
        icon = None

        if icon_path:
            # Check if this is an animated button and use current frame
            if key_index is not None and key_index in self.animated_buttons:
                anim_data = self.animated_buttons[key_index]
                icon = anim_data['frames'][anim_data['current_frame']].copy()
                icon_loaded = True
            else:
                icon_file = self._find_icon(icon_path)
                if icon_file and os.path.exists(icon_file):
                    try:
                        # For static images and non-animated GIFs
                        icon = Image.open(icon_file)
                        icon_loaded = True
                    except Exception as e:
                        logger.warning(f"Failed to load icon {icon_file}: {e}")

        if icon_loaded and icon:
            try:
                # Icon always fills the entire button
                target_size = image_size  # Use full button size
                y_offset = 0

                # Convert RGBA to RGB if needed (for transparency handling)
                if icon.mode == 'RGBA':
                    # Create a new image with the background color and paste the icon
                    temp = Image.new('RGB', icon.size, bg_color)
                    temp.paste(icon, (0, 0), icon)
                    icon = temp

                # Calculate scale to fill button completely
                # Scale based on the dimension that needs less scaling (to fill whole button)
                scale_w = target_size[0] / icon.width
                scale_h = target_size[1] / icon.height
                scale = max(scale_w, scale_h)  # Use max to ensure full coverage

                # Resize the icon
                new_size = (int(icon.width * scale), int(icon.height * scale))
                icon = icon.resize(new_size, Image.Resampling.LANCZOS)

                # Crop to fit if oversized (center crop)
                if icon.width > target_size[0] or icon.height > target_size[1]:
                    left = (icon.width - target_size[0]) // 2
                    top = (icon.height - target_size[1]) // 2
                    right = left + target_size[0]
                    bottom = top + target_size[1]
                    icon = icon.crop((left, top, right, bottom))

                # Paste icon centered (or at 0,0 if full size)
                if icon.size == target_size:
                    icon_pos = (0, 0)  # Full button coverage
                else:
                    icon_pos = ((image_size[0] - icon.width) // 2,
                               (image_size[1] - icon.height) // 2 + y_offset)

                # Paste the icon (already converted to RGB if needed)
                image.paste(icon, icon_pos)
            except Exception as e:
                logger.warning(f"Failed to process icon: {e}")

        # Draw text (overlay on icon if present)
        text = button_config.get("text") or button_config.get("label", "")
        if text:
            font_name = style.get("font", "DejaVu Sans")
            font_size = style.get("font_size", 14)
            text_color = style.get("text_color", "#FFFFFF")

            # Try to load font, fall back to default if not found
            try:
                # Make font bold for better visibility over icons
                if icon_loaded and "Bold" not in font_name:
                    # Try to load bold variant
                    try:
                        font = ImageFont.truetype(font_name.replace("Sans", "Sans Bold"), font_size)
                    except:
                        font = ImageFont.truetype(font_name, font_size)
                else:
                    font = ImageFont.truetype(font_name, font_size)
            except:
                font = ImageFont.load_default()

            # Process multi-line text
            lines = text.split('\n')

            if icon_loaded:
                # Overlay text on icon with shadow for readability
                y_offset = image_size[1] - (len(lines) * (font_size + 2)) - 8

                for line in lines:
                    line_bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = line_bbox[2] - line_bbox[0]
                    text_x = (image_size[0] - line_width) // 2

                    # Draw shadow/outline for better readability
                    shadow_color = "#000000"
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx != 0 or dy != 0:
                                draw.text((text_x + dx, y_offset + dy), line,
                                        font=font, fill=shadow_color)

                    # Draw the actual text
                    draw.text((text_x, y_offset), line, font=font, fill=text_color)
                    y_offset += font_size + 2
            else:
                # Center text if no icon
                y_offset = (image_size[1] - (len(lines) * (font_size + 2))) // 2
                for line in lines:
                    line_bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = line_bbox[2] - line_bbox[0]
                    text_pos = ((image_size[0] - line_width) // 2, y_offset)
                    draw.text(text_pos, line, font=font, fill=text_color)
                    y_offset += font_size + 2

        return PILHelper.to_native_format(self.deck, image)

    def _find_icon(self, icon_path: str) -> Optional[str]:
        """Find icon file by name or path

        Searches in the following order:
        1. Absolute path (with ~ expansion)
        2. Relative to ~/.decky/
        3. Relative to config file directory
        4. In ~/.decky/icons/ directory
        5. In legacy images/ directory (for backward compatibility)
        """
        # Expand user home directory
        icon_path = os.path.expanduser(icon_path)

        # If it's already an absolute path
        if os.path.isabs(icon_path):
            return icon_path if os.path.exists(icon_path) else None

        # Try relative to ~/.decky/
        decky_home = Path.home() / ".decky"
        possible_path = decky_home / icon_path
        if possible_path.exists():
            return str(possible_path)

        # Try relative to config file directory
        config_dir = self.config_path.parent
        possible_path = config_dir / icon_path
        if possible_path.exists():
            return str(possible_path)

        # Try in ~/.decky/icons/ directory (without full path)
        icons_dir = decky_home / "icons"
        if icons_dir.exists():
            possible_path = icons_dir / icon_path
            if possible_path.exists():
                return str(possible_path)

        # Legacy: Check in images directory relative to the project
        images_dir = self.config_path.parent.parent / "images"
        if images_dir.exists():
            # Try with common extensions
            for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                legacy_path = images_dir / f"{icon_path}{ext}"
                if legacy_path.exists():
                    return str(legacy_path)

            # Try as-is (might already have extension)
            legacy_path = images_dir / icon_path
            if legacy_path.exists():
                return str(legacy_path)

        return None

    def _update_page(self):
        """Update all buttons for current page"""
        page_config = self.pages.get(self.current_page, {})
        buttons = page_config.get("buttons", {})

        # Clear animated buttons when changing pages
        self.animated_buttons.clear()

        # Clear all buttons first
        for key in range(self.deck.key_count()):
            self.deck.set_key_image(key, PILHelper.to_native_format(
                self.deck,
                Image.new("RGB", self.deck.key_image_format()['size'], color="black")
            ))

        # Update configured buttons
        for button_num, button_config in buttons.items():
            try:
                # Stream Deck uses 0-based indexing
                key_index = int(button_num) - 1
                if 0 <= key_index < self.deck.key_count():
                    # Check if this is an animated GIF
                    icon_path = button_config.get("icon", "")
                    if icon_path:
                        icon_file = self._find_icon(icon_path)
                        if icon_file and icon_file.lower().endswith('.gif'):
                            # Try to load animated frames
                            self._setup_animated_button(key_index, button_config, icon_file)

                    # Create and set initial image
                    image = self._create_button_image(button_config, key_index)
                    self.deck.set_key_image(key_index, image)
            except Exception as e:
                logger.error(f"Failed to update button {button_num}: {e}")

        # Synchronize all animated buttons to start at the same time
        current_time = time.time()
        for anim_data in self.animated_buttons.values():
            anim_data['last_update'] = current_time
            anim_data['current_frame'] = 0

    def _key_change_callback(self, deck, key, state):
        """Handle button press events"""
        logger.debug(f"Button {key} {'pressed' if state else 'released'}")

        if not state:  # Button released
            return

        # Get button configuration (convert 0-based to 1-based)
        button_num = key + 1
        logger.info(f"Button {button_num} pressed (0-based key: {key})")

        page_config = self.pages.get(self.current_page, {})
        button_config = page_config.get("buttons", {}).get(button_num)

        if not button_config:
            logger.warning(f"No configuration for button {button_num}")
            return

        # Visual feedback
        if self.config.get("feedback", {}).get("visual", True):
            self._flash_button(key)

        # Execute action
        action = button_config.get("action")
        if action:
            self._execute_action(action)

    def _flash_button(self, key: int):
        """Flash button for visual feedback"""
        # Store current image
        page_config = self.pages.get(self.current_page, {})
        button_config = page_config.get("buttons", {}).get(key + 1)

        if not button_config:
            return

        # Create inverted image for flash effect
        original = self._create_button_image(button_config)

        # Flash white
        flash_image = PILHelper.to_native_format(
            self.deck,
            Image.new("RGB", self.deck.key_image_format()['size'], color="white")
        )

        self.deck.set_key_image(key, flash_image)
        time.sleep(0.1)
        self.deck.set_key_image(key, original)

    def _execute_action(self, action: Dict):
        """Execute button action"""
        action_type = action.get("type")
        logger.info(f"Executing action: {action_type}")

        if action_type == "command":
            command = action.get("command")
            if command:
                logger.info(f"Executing command: {command}")
                try:
                    subprocess.Popen(command, shell=True)
                except Exception as e:
                    logger.error(f"Failed to execute command: {e}")

        elif action_type == "keypress":
            keys = action.get("keys", [])
            self._send_keypress(keys)

        elif action_type == "page":
            page = action.get("page")
            if page in self.pages:
                logger.info(f"Switching to page: {page}")
                self.current_page = page
                self._update_page()
            else:
                logger.warning(f"Page not found: {page}")

        elif action_type == "brightness":
            change = action.get("change", 0)
            current = self.deck.get_brightness()
            new_brightness = max(0, min(100, current + change))
            self.deck.set_brightness(new_brightness)
            logger.info(f"Brightness changed to {new_brightness}%")

        elif action_type == "multi":
            actions = action.get("actions", [])
            for sub_action in actions:
                self._execute_action(sub_action)
                time.sleep(0.1)  # Small delay between actions

        else:
            logger.warning(f"Unknown action type: {action_type}")

    def _send_keypress(self, keys: List[str]):
        """Send keypress using xdotool"""
        if not keys:
            return

        # Map key names to xdotool format
        key_map = {
            "ctrl": "ctrl",
            "control": "ctrl",
            "alt": "alt",
            "shift": "shift",
            "super": "super",
            "cmd": "super",
            "win": "super",
        }

        # Convert keys to xdotool format
        xdo_keys = []
        for key in keys:
            mapped_key = key_map.get(key.lower(), key)
            xdo_keys.append(mapped_key)

        # Build xdotool command
        key_combo = "+".join(xdo_keys)
        command = f"xdotool key {key_combo}"

        logger.info(f"Sending keypress: {key_combo}")
        try:
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            logger.error(f"Failed to send keypress: {e}")

    def run(self):
        """Main run loop"""
        if not self.connect():
            return

        # Initial page update
        self._update_page()

        # Set up config file watcher
        config_mtime = os.path.getmtime(self.config_path)

        logger.info("Decky is running. Press Ctrl+C to exit.")

        try:
            while True:
                # Check for config file changes
                try:
                    current_mtime = os.path.getmtime(self.config_path)
                    if current_mtime > config_mtime:
                        config_mtime = current_mtime
                        self.reload_config()
                except:
                    pass

                # Update animated buttons
                if self.animated_buttons:
                    self._update_animations()

                time.sleep(0.05)  # 50ms update rate for smooth animations

        except KeyboardInterrupt:
            logger.info("Shutting down...")

        finally:
            if self.deck:
                self.deck.reset()
                self.deck.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Decky - YAML-driven Stream Deck controller")
    parser.add_argument(
        "config",
        nargs="?",
        default="configs/example.yaml",
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Check config file exists
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)

    # Run controller
    controller = DeckyController(args.config)
    controller.run()


if __name__ == "__main__":
    main()