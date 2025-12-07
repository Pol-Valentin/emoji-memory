import time

from loguru import logger as log

from src.backend.PluginManager.InputBases import KeyAction


class ScoreDisplay(KeyAction):
    """Score/timer display - short press to restart, hold to go back"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.victory_state = False

    def on_ready(self) -> None:
        """Called when action is ready - set up the display"""
        # Register with plugin
        self.plugin_base.score_display_action = self
        self.victory_state = False
        self.update_display()
        self.set_background_color([50, 50, 80, 255])

    def on_tick(self) -> None:
        """Called every second - update the display"""
        if not self.victory_state:
            self.update_display()

    def update_display(self) -> None:
        """Update the score and timer display"""
        state = self.plugin_base.game_state

        if not state["game_active"] or state["start_time"] is None:
            self.set_center_label(text="--:--\n0", font_size=14)
            return

        # Calculate elapsed time
        elapsed = int(time.time() - state["start_time"])
        minutes = elapsed // 60
        seconds = elapsed % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        # Get moves count
        moves = state["moves"]

        # Display format: time on top, moves below
        display_text = f"{time_str}\n{moves}"
        self.set_center_label(text=display_text, font_size=14)

    def on_key_down(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_up(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def on_key_short_up(self, *args, **kwargs) -> None:
        """Short press - restart game if victory, otherwise no action"""
        if self.victory_state:
            log.info("Restarting game after victory")
            self.victory_state = False
            self.plugin_base.create_game_page(self.deck_controller)

    def on_key_hold_start(self, *args, **kwargs) -> None:
        """Hold start - go back to previous page"""
        log.info("Hold on score display - going back")
        self.plugin_base.go_back(self.deck_controller)

    def on_key_hold_stop(self, *args, **kwargs) -> None:
        """Override to accept args"""
        pass

    def show_victory_score(self, moves: int, elapsed: int) -> None:
        """Show victory score"""
        self.victory_state = True
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.set_center_label(f"WIN!\n{moves} coups\n{minutes:02d}:{seconds:02d}", font_size=12)
        self.set_background_color([40, 150, 40, 255])  # Green
