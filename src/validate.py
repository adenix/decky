#!/usr/bin/env python3
"""
Configuration validator for Decky YAML files
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple


class ConfigValidator:
    """Validate Decky configuration files"""

    VALID_ACTION_TYPES = ["command", "keypress", "page", "brightness", "multi"]
    VALID_DEVICE_KEYS = ["brightness", "rotation"]
    VALID_STYLE_KEYS = ["font", "font_size", "text_color", "background_color"]

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML syntax: {e}")
            return False, self.errors, self.warnings
        except FileNotFoundError:
            self.errors.append(f"Configuration file not found: {self.config_path}")
            return False, self.errors, self.warnings

        # Validate structure
        self._validate_device(config.get("device", {}))
        self._validate_styles(config.get("styles", {}))
        self._validate_pages(config.get("pages", {}))

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_device(self, device: Dict):
        """Validate device configuration"""
        if not device:
            return

        for key in device:
            if key not in self.VALID_DEVICE_KEYS:
                self.warnings.append(f"Unknown device key: {key}")

        if "brightness" in device:
            brightness = device["brightness"]
            if not isinstance(brightness, int) or brightness < 0 or brightness > 100:
                self.errors.append(f"Invalid brightness value: {brightness} (must be 0-100)")

        if "rotation" in device:
            rotation = device["rotation"]
            if rotation not in [0, 90, 180, 270]:
                self.errors.append(f"Invalid rotation value: {rotation} (must be 0, 90, 180, or 270)")

    def _validate_styles(self, styles: Dict):
        """Validate style definitions"""
        for style_name, style in styles.items():
            if not isinstance(style, dict):
                self.errors.append(f"Style '{style_name}' must be a dictionary")
                continue

            for key in style:
                if key not in self.VALID_STYLE_KEYS:
                    self.warnings.append(f"Unknown style key in '{style_name}': {key}")

            # Validate color formats
            for color_key in ["text_color", "background_color"]:
                if color_key in style:
                    color = style[color_key]
                    if not self._is_valid_color(color):
                        self.errors.append(f"Invalid color format in style '{style_name}': {color}")

    def _validate_pages(self, pages: Dict):
        """Validate page configurations"""
        if not pages:
            self.errors.append("No pages defined in configuration")
            return

        page_names = set()
        for page_name, page in pages.items():
            page_names.add(page_name)

            if not isinstance(page, dict):
                self.errors.append(f"Page '{page_name}' must be a dictionary")
                continue

            buttons = page.get("buttons", {})
            if not buttons:
                self.warnings.append(f"Page '{page_name}' has no buttons defined")
                continue

            for button_num, button in buttons.items():
                self._validate_button(page_name, button_num, button, page_names)

    def _validate_button(self, page_name: str, button_num, button: Dict, page_names: set):
        """Validate button configuration"""
        try:
            button_int = int(button_num)
            if button_int < 1 or button_int > 32:  # Support up to XL
                self.warnings.append(f"Button {button_num} on page '{page_name}' may be out of range")
        except ValueError:
            self.errors.append(f"Invalid button number on page '{page_name}': {button_num}")

        # Check for label or text
        if "label" not in button and "text" not in button and "icon" not in button:
            self.warnings.append(f"Button {button_num} on page '{page_name}' has no label, text, or icon")

        # Validate action
        action = button.get("action")
        if not action:
            self.warnings.append(f"Button {button_num} on page '{page_name}' has no action defined")
        else:
            self._validate_action(page_name, button_num, action, page_names)

        # Validate style reference
        if "style" in button:
            # Note: We can't validate if the style exists without the full config context
            pass

    def _validate_action(self, page_name: str, button_num, action: Dict, page_names: set):
        """Validate button action"""
        action_type = action.get("type")

        if not action_type:
            self.errors.append(f"Button {button_num} on page '{page_name}' has no action type")
            return

        if action_type not in self.VALID_ACTION_TYPES:
            self.errors.append(f"Invalid action type for button {button_num} on page '{page_name}': {action_type}")
            return

        # Type-specific validation
        if action_type == "command":
            if "command" not in action:
                self.errors.append(f"Command action for button {button_num} on page '{page_name}' missing 'command'")

        elif action_type == "keypress":
            if "keys" not in action:
                self.errors.append(f"Keypress action for button {button_num} on page '{page_name}' missing 'keys'")
            elif not isinstance(action["keys"], list):
                self.errors.append(f"Keypress 'keys' for button {button_num} on page '{page_name}' must be a list")

        elif action_type == "page":
            if "page" not in action:
                self.errors.append(f"Page action for button {button_num} on page '{page_name}' missing 'page'")
            else:
                target_page = action["page"]
                # We'll check if the page exists after all pages are loaded
                if target_page not in page_names and target_page != page_name:
                    self.warnings.append(f"Page action references unknown page: {target_page}")

        elif action_type == "brightness":
            if "change" not in action:
                self.errors.append(f"Brightness action for button {button_num} on page '{page_name}' missing 'change'")

        elif action_type == "multi":
            if "actions" not in action:
                self.errors.append(f"Multi action for button {button_num} on page '{page_name}' missing 'actions'")
            elif not isinstance(action["actions"], list):
                self.errors.append(f"Multi 'actions' for button {button_num} on page '{page_name}' must be a list")
            else:
                for sub_action in action["actions"]:
                    self._validate_action(page_name, button_num, sub_action, page_names)

    def _is_valid_color(self, color: str) -> bool:
        """Check if color is valid hex format"""
        if not isinstance(color, str):
            return False
        if not color.startswith("#"):
            return False
        if len(color) not in [4, 7]:  # #RGB or #RRGGBB
            return False
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate Decky configuration files")
    parser.add_argument("config", help="Path to YAML configuration file")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only show errors")

    args = parser.parse_args()

    validator = ConfigValidator(args.config)
    valid, errors, warnings = validator.validate()

    # Print results
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()

    if warnings and not args.quiet:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if valid:
        print(f"✅ Configuration is valid!")
        if warnings:
            print(f"   ({len(warnings)} warning{'s' if len(warnings) != 1 else ''})")
    else:
        print(f"❌ Configuration has {len(errors)} error{'s' if len(errors) != 1 else ''}")
        sys.exit(1)


if __name__ == "__main__":
    main()