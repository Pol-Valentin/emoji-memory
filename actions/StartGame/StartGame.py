from loguru import logger as log

from src.backend.PluginManager.InputBases import KeyAction


class StartGame(KeyAction):
    """Action to start a new memory game"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self) -> None:
        """Called when action is ready - set up the button display"""
        self.set_center_label(
            text=self.plugin_base.lm.get("actions.startgame.label"),
            font_size=16
        )
        self.set_background_color([40, 120, 80, 255])  # Green

    def on_key_short_up(self, *args, **kwargs) -> None:
        """Called when key is released - start a new game"""
        log.info("Starting new memory game")
        self.plugin_base.create_game_page(self.deck_controller)
