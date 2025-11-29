"""
Animation management for Stream Deck buttons.

Handles GIF animations including frame loading, timing, and rendering.
"""

import logging
import time
from typing import Any, Dict, Optional

from PIL import Image

logger = logging.getLogger(__name__)


class AnimationManager:
    """
    Manages animated GIF buttons.

    Responsibilities:
    - Loading and caching GIF frames
    - Frame timing and advancement
    - Synchronized animation updates
    """

    # Animation update interval for smooth playback
    UPDATE_INTERVAL = 0.05  # 50ms = 20 FPS

    def __init__(self, button_renderer):
        """
        Initialize the animation manager.

        Args:
            button_renderer: ButtonRenderer instance for rendering frames
        """
        self.button_renderer = button_renderer
        self.animated_buttons: Dict[int, Dict[str, Any]] = {}
        self._last_update = 0.0

    def setup_animated_button(
        self, key_index: int, button_config: Dict[str, Any], icon_file: str
    ) -> bool:
        """
        Set up animated GIF frames for a button.

        Args:
            key_index: Zero-based key index
            button_config: Button configuration from YAML
            icon_file: Path to GIF file

        Returns:
            True if animation was set up successfully, False otherwise
        """
        try:
            gif = Image.open(icon_file)
            if not (hasattr(gif, "is_animated") and gif.is_animated):
                logger.debug(f"File {icon_file} is not an animated GIF")
                return False

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
                return True

            return False

        except FileNotFoundError as e:
            logger.warning(f"GIF file not found {icon_file}: {e}")
            return False
        except OSError as e:
            logger.warning(f"Cannot read GIF file {icon_file}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading GIF {icon_file}: {e}", exc_info=True)
            return False

    def render_current_frame(
        self, key_index: int, styles: Dict[str, Any], deck: Any
    ) -> Optional[bytes]:
        """
        Render the current frame for an animated button.

        Args:
            key_index: Zero-based key index
            styles: Style configuration dictionary
            deck: Stream Deck device instance

        Returns:
            Rendered frame as bytes, or None if button not animated
        """
        if key_index not in self.animated_buttons:
            return None

        anim_data = self.animated_buttons[key_index]
        frame = anim_data["frames"][anim_data["current_frame"]]
        button_config = anim_data["config"]

        return self.button_renderer.render_button_with_icon(button_config, styles, deck, frame)

    def update_animations(self, deck: Any) -> None:
        """
        Update all animated buttons.

        Advances frames based on timing and updates button images on the deck.

        Args:
            deck: Stream Deck device instance
        """
        if not deck or not self.animated_buttons:
            return

        current_time = time.time()

        # Throttle updates to target frame rate
        if current_time - self._last_update < self.UPDATE_INTERVAL:
            return

        # Update each animated button
        for _key_index, anim_data in list(self.animated_buttons.items()):
            # Check if it's time to advance to next frame
            frame_duration = anim_data["durations"][anim_data["current_frame"]] / 1000.0
            if current_time - anim_data["last_update"] >= frame_duration:
                # Advance to next frame
                anim_data["current_frame"] = (anim_data["current_frame"] + 1) % len(
                    anim_data["frames"]
                )
                anim_data["last_update"] = current_time

                # Update button image with new frame
                # Note: We can't render here without access to styles/config
                # This will be handled by the controller calling render_current_frame

        self._last_update = current_time

    def synchronize_animations(self) -> None:
        """
        Synchronize all animated buttons to start at the same time.

        Called when switching pages to ensure all GIFs animate in sync.
        """
        if not self.animated_buttons:
            return

        current_time = time.time()
        for anim_data in self.animated_buttons.values():
            anim_data["last_update"] = current_time
            anim_data["current_frame"] = 0

        logger.debug(f"Synchronized {len(self.animated_buttons)} animated buttons")

    def clear_animations(self) -> None:
        """Clear all animated button data (called when switching pages)."""
        self.animated_buttons.clear()
        logger.debug("Cleared all animated buttons")

    def has_animations(self) -> bool:
        """Check if there are any active animations."""
        return len(self.animated_buttons) > 0

    def get_animation_count(self) -> int:
        """Get the count of currently animated buttons."""
        return len(self.animated_buttons)
