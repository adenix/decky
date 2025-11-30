"""
Page management for Stream Deck button layouts.

Handles page rendering, button updates, and page navigation.
"""

import logging
import os
from typing import Any, Dict, Optional

from ..device.renderer import ButtonRenderer
from .animation import AnimationManager

logger = logging.getLogger(__name__)


class PageManager:
    """
    Manages Stream Deck pages and button rendering.

    Responsibilities:
    - Rendering pages and buttons
    - Page navigation
    - Icon file resolution
    - Integration with animation system
    """

    def __init__(self, button_renderer: ButtonRenderer, animation_manager: AnimationManager):
        """
        Initialize the page manager.

        Args:
            button_renderer: Renderer for creating button images
            animation_manager: Manager for handling animations
        """
        self.button_renderer = button_renderer
        self.animation_manager = animation_manager
        self.current_page = "main"

    def switch_page(self, page_name: str, deck: Any, config: Dict[str, Any]) -> bool:
        """
        Switch to a different page.

        Args:
            page_name: Name of page to switch to
            deck: Stream Deck device instance
            config: Full configuration dictionary

        Returns:
            True if page switch was successful, False otherwise
        """
        if page_name not in config.get("pages", {}):
            logger.error(f"Page '{page_name}' not found in configuration")
            return False

        logger.info(f"Switching to page: {page_name}")
        self.current_page = page_name
        self.update_page(deck, config)
        return True

    def update_page(self, deck: Any, config: Dict[str, Any]) -> None:
        """
        Update all buttons for the current page.

        Args:
            deck: Stream Deck device instance
            config: Full configuration dictionary
        """
        if not deck:
            logger.warning("Cannot update page - no deck connected")
            return

        page_config = config.get("pages", {}).get(self.current_page, {})
        buttons = page_config.get("buttons", {})
        styles = config.get("styles", {})

        # Clear animated buttons from previous page
        self.animation_manager.clear_animations()

        # Clear all buttons to black first (prevents retention issues)
        blank_image = self.button_renderer.render_blank(deck)
        for key in range(deck.key_count()):
            deck.set_key_image(key, blank_image)

        # Render each button
        for key in range(deck.key_count()):
            button_num = key + 1
            button_config = buttons.get(button_num, {})

            if button_config:
                self._render_button(key, button_config, styles, deck)

        # Synchronize all animated buttons to start at the same time
        if self.animation_manager.has_animations():
            self.animation_manager.synchronize_animations()
            logger.debug(
                f"Page loaded with {self.animation_manager.get_animation_count()} animations"
            )

    def _render_button(
        self, key: int, button_config: Dict[str, Any], styles: Dict[str, Any], deck: Any
    ) -> None:
        """
        Render a single button.

        Handles both static and animated buttons.

        Args:
            key: Zero-based key index
            button_config: Configuration for this button
            styles: Style configuration dictionary
            deck: Stream Deck device instance
        """
        # Check for animated GIFs
        icon_path = button_config.get("icon")
        if icon_path and icon_path.lower().endswith(".gif"):
            icon_file = self._find_icon(icon_path)
            if icon_file:
                # Try to set up animation
                if self.animation_manager.setup_animated_button(key, button_config, icon_file):
                    # Render initial frame
                    frame_image = self.animation_manager.render_current_frame(key, styles, deck)
                    if frame_image:
                        deck.set_key_image(key, frame_image)
                    return  # Animation set up successfully

        # Render static button
        image = self.button_renderer.render_button(button_config, styles, deck)
        deck.set_key_image(key, image)

    def update_animated_buttons(self, deck: Any, config: Dict[str, Any]) -> None:
        """
        Update all animated button frames.

        Should be called frequently (20-30 FPS) for smooth animations.

        Args:
            deck: Stream Deck device instance
            config: Full configuration dictionary
        """
        if not deck or not self.animation_manager.has_animations():
            return

        self.animation_manager.update_animations(deck)

        # Render updated frames
        styles = config.get("styles", {})
        for key_index in list(self.animation_manager.animated_buttons.keys()):
            frame_image = self.animation_manager.render_current_frame(key_index, styles, deck)
            if frame_image:
                deck.set_key_image(key_index, frame_image)

    def _find_icon(self, icon_path: str) -> Optional[str]:
        """
        Find icon file in the icons directory.

        Args:
            icon_path: Icon path from configuration

        Returns:
            Full path to icon file, or None if not found
        """
        if not icon_path:
            return None

        # Expand user path
        icon_path = os.path.expanduser(icon_path)

        # Check if it's an absolute path
        if os.path.isabs(icon_path):
            return icon_path if os.path.exists(icon_path) else None

        # Otherwise, treat as relative to ~/.decky/
        base_path = os.path.expanduser("~/.decky")
        full_path = os.path.join(base_path, icon_path)

        if os.path.exists(full_path):
            return full_path

        return None
