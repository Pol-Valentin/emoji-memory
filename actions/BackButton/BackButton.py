from loguru import logger as log

from src.backend.PluginManager.InputBases import KeyAction


class BackButton(KeyAction):
    """Button to return to the previous page"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_ready(self) -> None:
        """Called when action is ready - set up the button display"""
        self.set_center_label(
            text=self.plugin_base.lm.get("actions.backbutton.label"),
            font_size=20
        )
        self.set_background_color([70, 70, 70, 255])

    def on_key_short_up(self, *args, **kwargs) -> None:
        """Called when key is released - go back to previous page"""
        log.info("Going back to previous page")
        self.plugin_base.go_back(self.deck_controller)
