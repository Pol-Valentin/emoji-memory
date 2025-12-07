import threading

from loguru import logger as log

from src.backend.PluginManager.InputBases import KeyAction


class MemoryCard(KeyAction):
    """Memory card that can be flipped to reveal an emoji"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_index = None

    def on_ready(self) -> None:
        """Called when action is ready - show card back"""
        settings = self.get_settings()
        self.card_index = settings.get("card_index")

        if self.card_index is not None:
            # Register with plugin
            self.plugin_base.register_action(self.card_index, self)

            # Check if card should be shown as matched
            state = self.plugin_base.game_state
            if self.card_index in state["matched"]:
                self.show_emoji()
            else:
                self.show_card_back()

    def show_card_back(self) -> None:
        """Show the back of the card (hidden state)"""
        card_back = self.plugin_base.get_card_back_path()
        if card_back and self._file_exists(card_back):
            self.set_media(media_path=card_back, size=0.9)
        else:
            # Fallback: show question mark
            self.set_center_label(text="?", font_size=32)
        self.set_background_color([60, 60, 100, 255])

    def show_emoji(self) -> None:
        """Show the emoji (revealed state)"""
        if self.card_index is None:
            return

        state = self.plugin_base.game_state
        if self.card_index >= len(state["cards"]):
            return

        codepoint = state["cards"][self.card_index]
        gif_path = self.plugin_base.get_emoji_gif_path(codepoint)

        if self._file_exists(gif_path):
            self.set_media(media_path=gif_path, size=0.9)
        else:
            # Fallback if GIF not found
            self.set_center_label(text="?", font_size=32)
            log.warning(f"Emoji GIF not found: {gif_path}")

        self.set_background_color([80, 80, 120, 255])

    def show_victory(self) -> None:
        """Show victory state"""
        self.set_background_color([40, 150, 40, 255])  # Green

    def show_matched(self) -> None:
        """Show matched state - card disappears"""
        self.set_media(media_path="", size=0)  # Clear image
        self.set_center_label("", font_size=1)  # Clear label
        self.set_background_color([30, 30, 30, 255])  # Dark background

    def _file_exists(self, path: str) -> bool:
        """Check if file exists"""
        import os
        return os.path.exists(path)

    def on_key_down(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_up(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_hold_start(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_hold_stop(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_short_up(self, *args, **kwargs) -> None:
        """Called when key is released (short press) - flip the card"""
        # Re-read settings in case action was recreated
        settings = self.get_settings()
        self.card_index = settings.get("card_index")

        log.info(f"Card clicked: index={self.card_index}")

        if self.card_index is None:
            log.warning("No card_index in settings")
            return

        state = self.plugin_base.game_state
        log.info(f"Game state: active={state['game_active']}, cards={len(state['cards'])}")
        if not state["game_active"]:
            return

        # Ignore if already revealed or matched
        if self.card_index in state["revealed"] or self.card_index in state["matched"]:
            return

        # Reveal this card
        self.show_emoji()
        state["revealed"].append(self.card_index)

        if state["first_card"] is None:
            # First card of the turn
            state["first_card"] = self.card_index
        else:
            # Second card - check for match
            state["moves"] += 1
            first_idx = state["first_card"]
            first_codepoint = state["cards"][first_idx]
            second_codepoint = state["cards"][self.card_index]

            if first_codepoint == second_codepoint:
                # Match!
                log.info(f"Match found! {first_codepoint}")
                state["matched"].extend([first_idx, self.card_index])
                state["first_card"] = None
                state["revealed"] = []

                # Check for victory
                is_victory = len(state["matched"]) == len(state["cards"])
                log.info(f"Matched: {len(state['matched'])}/{len(state['cards'])} - Victory: {is_victory}")

                # Hide matched cards after a short delay to show the match
                threading.Timer(
                    0.5,
                    self.plugin_base.clear_matched_cards,
                    args=[first_idx, self.card_index]
                ).start()

                if is_victory:
                    threading.Timer(
                        0.7,
                        self.plugin_base.show_victory
                    ).start()
            else:
                # No match - hide cards after delay
                state["first_card"] = None
                idx1, idx2 = first_idx, self.card_index
                threading.Timer(
                    1.0,
                    self.plugin_base.hide_cards,
                    args=[idx1, idx2]
                ).start()
