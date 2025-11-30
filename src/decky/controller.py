"""
Main controller for Decky Stream Deck - Refactored with managers.
"""

import logging
import time
from typing import Any, Dict, Optional

from .actions.base import ActionContext
from .actions.registry import registry
from .config.loader import ConfigLoader
from .device.manager import DeviceManager
from .device.renderer import ButtonRenderer
from .managers import AnimationManager, ConnectionManager, PageManager, WidgetManager
from .platforms import detect_platform
from .platforms.base import Platform

logger = logging.getLogger(__name__)


class DeckyController:
    """
    Main controller orchestrating Stream Deck operations.

    This controller delegates specific responsibilities to specialized managers:
    - ConnectionManager: Handles device connection lifecycle
    - AnimationManager: Manages GIF animations
    - PageManager: Handles page rendering and button updates
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize the Decky controller.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path: str = config_path
        self.config: Optional[Dict[str, Any]] = None
        self.running: bool = False

        # Platform detection
        self.platform: Optional[Platform] = detect_platform()
        logger.info(f"Detected platform: {self.platform.name if self.platform else 'generic'}")

        # Initialize core components
        self.config_loader: ConfigLoader = ConfigLoader()
        self.device_manager: DeviceManager = DeviceManager()
        self.button_renderer: ButtonRenderer = ButtonRenderer()

        # Initialize managers
        self.animation_manager = AnimationManager(self.button_renderer)
        self.widget_manager = WidgetManager(self.button_renderer, self.animation_manager)
        self.connection_manager = ConnectionManager(
            device_manager=self.device_manager,
            platform=self.platform,
            on_connected=self._on_device_connected,
            on_disconnected=self._on_device_disconnected,
        )
        self.page_manager = PageManager(
            self.button_renderer, self.animation_manager, self.widget_manager
        )

        # Register all actions
        registry.auto_discover()
        logger.info(f"Registered actions: {registry.list_actions()}")

        # Register all widgets
        self.widget_manager.widget_registry.auto_discover()
        logger.info(f"Registered widgets: {self.widget_manager.widget_registry.list_widgets()}")

    @property
    def deck(self) -> Optional[Any]:
        """Get current deck reference from connection manager."""
        return self.connection_manager.deck

    @property
    def current_page(self) -> str:
        """Get current page name."""
        return self.page_manager.current_page

    @property
    def is_locked(self) -> bool:
        """Get screen lock status from connection manager."""
        return self.connection_manager.is_locked

    @property
    def animated_buttons(self) -> Dict[int, Dict[str, Any]]:
        """Get animated buttons dict from animation manager."""
        return self.animation_manager.animated_buttons

    @property
    def shutting_down(self) -> bool:
        """Get shutting down flag from connection manager."""
        return self.connection_manager.shutting_down

    @shutting_down.setter
    def shutting_down(self, value: bool) -> None:
        """Set shutting down flag in connection manager."""
        self.connection_manager.shutting_down = value

    def load_config(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self.config_loader.load(self.config_path)
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False

    def connect(self) -> bool:
        """
        Establish connection to a Stream Deck device.

        Returns:
            True if connection successful, False otherwise.
        """
        return self.connection_manager.connect()

    def _on_device_connected(self, deck: Any) -> None:
        """
        Callback when device connects.

        Sets up device brightness, callbacks, and renders initial page.

        Args:
            deck: Newly connected Stream Deck device
        """
        try:
            # Configure device brightness from settings
            brightness = self.config.get("device", {}).get("brightness", 100)
            deck.set_brightness(brightness)
            logger.debug(f"Stream Deck brightness set to {brightness}%")

            # Register key press callback
            deck.set_key_callback(self._key_callback)
            logger.debug("Key press callback registered")

            # Render current page buttons
            self.page_manager.update_page(deck, self.config)
            logger.debug(f"Initial page '{self.current_page}' rendered")

        except Exception as e:
            logger.error(f"Error during Stream Deck setup: {e}", exc_info=True)

    def _on_device_disconnected(self) -> None:
        """Callback when device disconnects."""
        logger.debug("Device disconnected callback triggered")

    def _key_callback(self, deck: Any, key: int, state: bool) -> None:
        """
        Handle key press events.

        Args:
            deck: StreamDeck device instance
            key: Zero-based key index
            state: True for press, False for release
        """
        if not state:  # Key release
            return

        logger.info(f"Button {key + 1} pressed (0-based key: {key})")

        page_config = self.config.get("pages", {}).get(self.current_page, {})
        button_config = page_config.get("buttons", {}).get(key + 1)

        if not button_config:
            logger.debug(f"No configuration for button {key + 1}")
            return

        action_config = button_config.get("action", {})
        action_type = action_config.get("type")

        if not action_type:
            logger.debug(f"No action type for button {key + 1}")
            return

        # Execute action using the registry
        action = registry.get_action(action_type)
        if action:
            context = ActionContext(controller=self, button_config=button_config, key_index=key)

            # Handle page switching specially
            if action_type == "page":
                new_page = action_config.get("page")
                if new_page:
                    self.page_manager.switch_page(new_page, deck, self.config)
            else:
                # Execute other actions
                success = action.execute(context, action_config)
                if not success:
                    logger.warning(f"Action {action_type} failed for button {key + 1}")
        else:
            logger.error(f"Unknown action type: {action_type}")

    def run(self) -> None:
        """
        Main application run loop.

        Handles the primary application lifecycle including:
        - Initial device connection
        - USB hot-plug detection and reconnection
        - Screen lock monitoring
        - Graceful shutdown
        """
        # Load configuration file
        if not self.load_config():
            logger.error("Cannot start without valid configuration")
            return

        # Initial connection attempt (OK if no device present)
        if not self.connect():
            logger.info("Starting without Stream Deck - will connect when available")

        self.running = True

        # Start connection monitoring in background
        self.connection_manager.start_monitoring()
        logger.info("Decky is running. Press Ctrl+C to exit.")

        try:
            while self.running:
                # Update animations and widgets if we have a deck
                if self.deck:
                    self.page_manager.update_animated_buttons(self.deck, self.config)

                    # Update widgets that need refreshing
                    widget_updates = self.widget_manager.update_widgets(
                        self.deck, self.config.get("styles", {})
                    )
                    for key_index, image in widget_updates.items():
                        self.deck.set_key_image(key_index, image)

                # Short sleep to prevent CPU spinning
                time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            # Clean shutdown
            logger.info("Shutting down Decky...")
            self.running = False

            # Stop connection monitoring
            self.connection_manager.stop_monitoring()

            # Disconnect device if still connected
            if self.deck:
                self.connection_manager.disconnect()
