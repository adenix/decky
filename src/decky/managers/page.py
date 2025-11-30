"""
Page management for Stream Deck button layouts.

Handles page rendering, button updates, and page navigation.
"""

import copy
import logging
import os
import threading
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

    def __init__(self, button_renderer: ButtonRenderer, animation_manager: AnimationManager, widget_manager=None):
        """
        Initialize the page manager.

        Args:
            button_renderer: Renderer for creating button images
            animation_manager: Manager for handling animations
            widget_manager: Manager for handling widgets (optional for backward compatibility)
        """
        self.button_renderer = button_renderer
        self.animation_manager = animation_manager
        self.widget_manager = widget_manager
        self.current_page = "main"
        self._page_lock = threading.Lock()  # Prevent concurrent page/animation updates

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

        # Lock to prevent animation updates during page rendering
        with self._page_lock:
            page_config = config.get("pages", {}).get(self.current_page, {})
            buttons = page_config.get("buttons", {})
            styles = config.get("styles", {})

            # Clear animated buttons and widgets from previous page
            self.animation_manager.clear_animations()
            if self.widget_manager:
                self.widget_manager.clear_widgets()

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

        Handles static, animated, and widget buttons.

        Args:
            key: Zero-based key index
            button_config: Configuration for this button
            styles: Style configuration dictionary
            deck: Stream Deck device instance
        """
        # First, check for animated GIF backgrounds (must be done before widget setup)
        # This allows widgets to have animated backgrounds
        icon_path = button_config.get("icon")
        has_animated_background = False
        if icon_path and icon_path.lower().endswith(".gif"):
            icon_file = self._find_icon(icon_path)
            if icon_file:
                # Set up animation for the background
                if self.animation_manager.setup_animated_button(key, button_config, icon_file):
                    has_animated_background = True

        # Check if this is a widget button
        if "widget" in button_config and self.widget_manager:
            if self.widget_manager.setup_widget_button(key, button_config, styles):
                # Render initial widget state
                # If there's an animated background, the widget will be rendered on top
                image = self.widget_manager.render_widget(key, styles, deck, force=True)
                if image:
                    deck.set_key_image(key, image)
                return  # Widget set up successfully

        # For non-widget buttons with animations, render the first frame
        if has_animated_background:
            frame_image = self.animation_manager.render_current_frame(key, styles, deck)
            if frame_image:
                deck.set_key_image(key, frame_image)
            return  # Animation set up successfully

        # Render static button (no widget, no animation)
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

        # Lock to prevent page updates during animation rendering
        # Use trylock to avoid blocking if page is being updated
        if not self._page_lock.acquire(blocking=False):
            # Page is being updated, skip this animation frame
            return

        try:
            self.animation_manager.update_animations(deck)

            # Render updated frames with layered compositing
            styles = config.get("styles", {})
            for key_index in list(self.animation_manager.animated_buttons.keys()):
                # Check if this button has a widget overlay
                if self.widget_manager and key_index in self.widget_manager.active_widgets:
                    # LAYERED RENDERING: Composite GIF background + widget text
                    widget_text = self.widget_manager.get_widget_text(key_index)
                    if widget_text is not None:
                        # Get widget's button config safely (thread-safe access)
                        try:
                            widget_data = self.widget_manager.active_widgets.get(key_index)
                            if not widget_data:
                                continue  # Widget was removed during iteration
                                
                            button_config = copy.deepcopy(widget_data["button_config"])
                            button_config["text"] = widget_text
                            
                            # Get current animation frame
                            anim_data = self.animation_manager.animated_buttons.get(key_index)
                            if not anim_data:
                                continue  # Animation was removed during iteration
                                
                            current_frame = anim_data["frames"][anim_data["current_frame"]]
                            
                            # Composite: render text over animation frame
                            frame_image = self.button_renderer.render_button_with_icon(
                                button_config, styles, deck, current_frame
                            )
                            if frame_image:
                                deck.set_key_image(key_index, frame_image)
                        except (KeyError, IndexError) as e:
                            # Widget or animation removed during render - skip this frame
                            logger.debug(f"Skipping frame for button {key_index}: {e}")
                    continue
                    
                # No widget: just render the animation frame
                frame_image = self.animation_manager.render_current_frame(
                    key_index, styles, deck
                )
                if frame_image:
                    deck.set_key_image(key_index, frame_image)
        finally:
            self._page_lock.release()

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
