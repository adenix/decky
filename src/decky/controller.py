"""
Main controller for Decky Stream Deck
"""

import logging
import os
import threading
import time
from typing import Any, Dict, Optional

from PIL import Image

from .actions.base import ActionContext
from .actions.registry import registry
from .config.loader import ConfigLoader
from .device.manager import DeviceManager as DeckManager
from .device.renderer import ButtonRenderer
from .platforms import detect_platform
from .platforms.base import Platform

logger = logging.getLogger(__name__)


class DeckyController:
    """Main controller orchestrating Stream Deck operations"""

    def __init__(self, config_path: str) -> None:
        self.config_path: str = config_path
        self.config: Optional[Dict[str, Any]] = None
        self.deck: Optional[Any] = None  # StreamDeck device object
        self.current_page: str = "main"
        self.running: bool = False
        self.shutting_down: bool = False  # Flag to prevent reconnection during shutdown
        self.lock_monitor_thread: Optional[threading.Thread] = None
        self.is_locked: bool = False
        self.animated_buttons: Dict[int, Dict[str, Any]] = {}
        self.animation_thread: Optional[threading.Thread] = None

        # Platform detection
        self.platform: Optional[Platform] = detect_platform()
        logger.info(f"Detected platform: {self.platform.name if self.platform else 'generic'}")

        # Initialize components
        self.config_loader: ConfigLoader = ConfigLoader()
        self.deck_manager: DeckManager = DeckManager()
        self.button_renderer: ButtonRenderer = ButtonRenderer()

        # Register all actions
        registry.auto_discover()
        logger.info(f"Registered actions: {registry.list_actions()}")

    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            self.config = self.config_loader.load(self.config_path)
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False

    def connect(self) -> bool:
        """
        Establish connection to a Stream Deck device.

        Attempts to connect to an available Stream Deck and configure it
        with the current settings. This method is safe to call multiple
        times and will handle reconnection scenarios.

        Returns:
            True if connection and setup successful, False otherwise.
        """
        try:
            logger.debug("Attempting to connect to Stream Deck...")
            self.deck = self.deck_manager.connect()

            if not self.deck:
                # No device found (expected case when unplugged)
                logger.debug("No Stream Deck device available")
                return False

            # Configure the newly connected device
            self._setup_deck()
            return True

        except Exception as e:
            logger.error(f"Unexpected error during Stream Deck connection: {e}", exc_info=True)
            self.deck = None  # Ensure deck is None on error
            return False

    def _setup_deck(self) -> None:
        """
        Configure a newly connected Stream Deck device.

        Sets up device brightness, key callbacks, and renders the initial
        button layout. This method assumes self.deck is valid.
        """
        if not self.deck:
            logger.warning("Setup called with no deck connected")
            return

        try:
            # Configure device brightness from settings
            brightness = self.config.get("device", {}).get("brightness", 100)
            self.deck.set_brightness(brightness)
            logger.debug(f"Stream Deck brightness set to {brightness}%")

            # Register key press callback
            self.deck.set_key_callback(self._key_callback)
            logger.debug("Key press callback registered")

            # Render current page buttons
            self._update_page()
            logger.debug(f"Initial page '{self.current_page}' rendered")

        except Exception as e:
            logger.error(f"Error during Stream Deck setup: {e}", exc_info=True)

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
                if new_page and new_page in self.config.get("pages", {}):
                    logger.info(f"Switching to page: {new_page}")
                    self.current_page = new_page
                    self._update_page()
            else:
                # Execute other actions
                success = action.execute(context, action_config)
                if not success:
                    logger.warning(f"Action {action_type} failed for button {key + 1}")
        else:
            logger.error(f"Unknown action type: {action_type}")

    def _update_page(self) -> None:
        """Update all buttons for current page"""
        if not self.deck:
            return

        page_config = self.config.get("pages", {}).get(self.current_page, {})
        buttons = page_config.get("buttons", {})

        # Clear animated buttons from previous page
        self.animated_buttons.clear()

        # Clear all buttons to black first (prevents retention issues)
        blank_image = self.button_renderer.render_blank(self.deck)
        for key in range(self.deck.key_count()):
            self.deck.set_key_image(key, blank_image)

        # Render each button
        for key in range(self.deck.key_count()):
            button_num = key + 1
            button_config = buttons.get(button_num, {})

            if button_config:
                # Check for animations
                icon_path = button_config.get("icon")
                if icon_path and icon_path.lower().endswith(".gif"):
                    # Set up animated GIF
                    icon_file = self._find_icon(icon_path)
                    if icon_file:
                        self._setup_animated_button(key, button_config, icon_file)
                        # Set initial frame
                        if key in self.animated_buttons:
                            frame_image = self._render_animated_frame(key)
                            if frame_image:
                                self.deck.set_key_image(key, frame_image)
                    else:
                        # GIF not found, render static
                        image = self.button_renderer.render_button(
                            button_config, self.config.get("styles", {}), self.deck
                        )
                        self.deck.set_key_image(key, image)
                else:
                    # Static image
                    image = self.button_renderer.render_button(
                        button_config, self.config.get("styles", {}), self.deck
                    )
                    self.deck.set_key_image(key, image)

        # Synchronize all animated buttons to start at the same time
        # This ensures all GIFs animate in sync
        if self.animated_buttons:
            current_time = time.time()
            for anim_data in self.animated_buttons.values():
                anim_data["last_update"] = current_time
                anim_data["current_frame"] = 0
            logger.debug(f"Synchronized {len(self.animated_buttons)} animated buttons")

    def _find_icon(self, icon_path: str) -> Optional[str]:
        """Find icon file in the icons directory."""
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

    def _setup_animated_button(
        self, key_index: int, button_config: Dict[str, Any], icon_file: str
    ) -> None:
        """Set up animated GIF frames for a button."""
        try:
            gif = Image.open(icon_file)
            if hasattr(gif, "is_animated") and gif.is_animated:
                frames = []
                durations = []

                for frame_num in range(gif.n_frames):
                    gif.seek(frame_num)
                    frame = gif.copy()
                    frames.append(frame)
                    durations.append(gif.info.get("duration", 100))

                if frames:
                    self.animated_buttons[key_index] = {
                        "frames": frames,
                        "durations": durations,
                        "current_frame": 0,
                        "last_update": time.time(),
                        "config": button_config,
                    }
                    logger.debug(f"Loaded {len(frames)} frames for animated button {key_index+1}")
        except Exception as e:
            logger.warning(f"Failed to load animated GIF {icon_file}: {e}")

    def _render_animated_frame(self, key_index: int) -> Optional[bytes]:
        """Render the current frame for an animated button."""
        if key_index not in self.animated_buttons:
            return None

        anim_data = self.animated_buttons[key_index]
        frame = anim_data["frames"][anim_data["current_frame"]]
        button_config = anim_data["config"]

        # Use button renderer to create the image with the current frame
        return self.button_renderer.render_button_with_icon(
            button_config, self.config.get("styles", {}), self.deck, frame
        )

    def _update_animations(self) -> None:
        """Update animated buttons."""
        if not self.deck or not self.animated_buttons:
            return

        current_time = time.time()

        # Create a copy of keys to avoid dictionary change during iteration
        for key_index, anim_data in list(self.animated_buttons.items()):
            # Check if it's time to advance to next frame
            frame_duration = (
                anim_data["durations"][anim_data["current_frame"]] / 1000.0
            )  # Convert ms to seconds
            if current_time - anim_data["last_update"] >= frame_duration:
                # Advance to next frame
                anim_data["current_frame"] = (anim_data["current_frame"] + 1) % len(
                    anim_data["frames"]
                )
                anim_data["last_update"] = current_time

                # Update button image with new frame
                frame_image = self._render_animated_frame(key_index)
                if frame_image:
                    self.deck.set_key_image(key_index, frame_image)

    def _monitor_screen_lock(self) -> None:
        """Monitor screen lock status"""
        while self.running:
            try:
                locked = self.platform.is_screen_locked() if self.platform else False

                if locked != self.is_locked:
                    self.is_locked = locked
                    if locked:
                        logger.info("Screen locked - disconnecting Stream Deck")
                        self._disconnect_deck()
                    elif not self.shutting_down:  # Only reconnect if not shutting down
                        logger.info("Screen unlocked - reconnecting Stream Deck")
                        if self.connect():
                            self._update_page()

                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in lock monitor: {e}")
                time.sleep(5)

    def _disconnect_deck(self) -> None:
        """
        Safely disconnect from the Stream Deck device.

        Handles both voluntary disconnection (screen lock) and involuntary
        disconnection (device unplugged). Always clears the deck reference
        regardless of errors.
        """
        if not self.deck:
            return

        logger.debug("Disconnecting from Stream Deck...")

        # Use device manager for clean disconnection
        clean_disconnect = self.deck_manager.disconnect(self.deck)

        # Always clear our reference
        self.deck = None

        if clean_disconnect:
            logger.info("Stream Deck disconnected")
        else:
            logger.info("Stream Deck disconnected (device was already unavailable)")

    def run(self) -> None:
        """
        Main application run loop.

        Handles the primary application lifecycle including:
        - Initial device connection
        - USB hot-plug detection and reconnection
        - Screen lock monitoring
        - Graceful shutdown

        The loop runs continuously until interrupted, checking device
        connectivity and attempting reconnection when needed.
        """
        # Load configuration file
        if not self.load_config():
            logger.error("Cannot start without valid configuration")
            return

        # Initial connection attempt (OK if no device present)
        if not self.connect():
            logger.info("Starting without Stream Deck - will connect when available")

        self.running = True

        # Start screen lock monitoring in background
        self.lock_monitor_thread = threading.Thread(
            target=self._monitor_screen_lock, daemon=True, name="ScreenLockMonitor"
        )
        self.lock_monitor_thread.start()
        logger.debug("Screen lock monitoring started")

        logger.info("Decky is running. Press Ctrl+C to exit.")

        # Reconnection timing configuration
        RECONNECT_INTERVAL = 2.0  # Seconds between reconnection attempts
        CONNECTION_CHECK_INTERVAL = 0.5  # How often to check connection status
        ANIMATION_UPDATE_INTERVAL = 0.05  # 50ms for smooth GIF animations (20 FPS)

        last_reconnect_attempt = 0
        last_connection_check = 0
        last_animation_update = 0

        try:
            while self.running:
                current_time = time.time()

                # Check connection health periodically
                if current_time - last_connection_check >= CONNECTION_CHECK_INTERVAL:
                    # Monitor existing connection health
                    if self.deck:
                        if not self.deck_manager.is_connected(self.deck):
                            # Device has been disconnected (unplugged)
                            logger.info("Stream Deck disconnected (device removed)")
                            self._disconnect_deck()
                            # Reset timer to attempt immediate reconnection
                            last_reconnect_attempt = 0

                    # Attempt reconnection if needed (but not if shutting down)
                    if not self.deck and not self.is_locked and not self.shutting_down:
                        # Throttle reconnection attempts to avoid USB enumeration spam
                        time_since_last_attempt = current_time - last_reconnect_attempt
                        if time_since_last_attempt >= RECONNECT_INTERVAL:
                            logger.debug("Checking for Stream Deck devices...")
                            if self.connect():
                                logger.info("Stream Deck connected and configured")
                            last_reconnect_attempt = current_time

                    last_connection_check = current_time

                # Update animated buttons more frequently for smooth animation
                if self.deck and self.animated_buttons:
                    if current_time - last_animation_update >= ANIMATION_UPDATE_INTERVAL:
                        self._update_animations()
                        last_animation_update = current_time

                # Short sleep to prevent CPU spinning
                time.sleep(0.01)  # 10ms sleep for responsive loop

        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        finally:
            # Clean shutdown
            logger.info("Shutting down Decky...")
            self.running = False
            self.shutting_down = True  # Ensure no reconnection attempts

            # Disconnect device if still connected
            if self.deck:
                self._disconnect_deck()
