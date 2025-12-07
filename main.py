import os
import json
import random
import time

from loguru import logger as log

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

import globals as gl

from .actions.StartGame.StartGame import StartGame
from .actions.MemoryCard.MemoryCard import MemoryCard
from .actions.BackButton.BackButton import BackButton
from .actions.ScoreDisplay.ScoreDisplay import ScoreDisplay


class EmojiMemory(PluginBase):
    def __init__(self):
        super().__init__()

        self.lm = self.locale_manager

        # Game state
        self.game_state = {
            "cards": [],              # List of emoji codepoints for each card
            "revealed": [],           # Indices of currently revealed cards
            "matched": [],            # Indices of matched cards
            "first_card": None,       # Index of first card in current turn
            "moves": 0,               # Number of moves
            "start_time": None,       # Game start time
            "deck_controller": None,  # Reference to deck controller
            "back_page": None,        # Page to return to
            "game_active": False,     # Is a game in progress
            "actions": {},            # Map of card_index to action instance
        }

        # Reference to score display action
        self.score_display_action = None

        # Load emoji index
        self.emoji_index = self.load_emoji_index()

        # Register actions
        self.start_game_holder = ActionHolder(
            plugin_base=self,
            action_base=StartGame,
            action_id="com_pol_emoji_memory::StartGame",
            action_name=self.lm.get("actions.startgame.name"),
        )
        self.add_action_holder(self.start_game_holder)

        self.memory_card_holder = ActionHolder(
            plugin_base=self,
            action_base=MemoryCard,
            action_id="com_pol_emoji_memory::MemoryCard",
            action_name=self.lm.get("actions.memorycard.name"),
        )
        self.add_action_holder(self.memory_card_holder)

        self.back_button_holder = ActionHolder(
            plugin_base=self,
            action_base=BackButton,
            action_id="com_pol_emoji_memory::BackButton",
            action_name=self.lm.get("actions.backbutton.name"),
        )
        self.add_action_holder(self.back_button_holder)

        self.score_display_holder = ActionHolder(
            plugin_base=self,
            action_base=ScoreDisplay,
            action_id="com_pol_emoji_memory::ScoreDisplay",
            action_name=self.lm.get("actions.scoredisplay.name"),
        )
        self.add_action_holder(self.score_display_holder)

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/music/emoji-memory",
            plugin_version="1.0.0",
            app_version="1.5.0-beta.6"
        )

    def load_emoji_index(self) -> list:
        """Load the emoji index from JSON file"""
        index_path = os.path.join(self.PATH, "assets", "emoji_index.json")
        if not os.path.exists(index_path):
            log.error("Emoji index not found! Run 'make download-emojis' first.")
            return []

        with open(index_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_emoji_gif_path(self, codepoint: str) -> str:
        """Return local path to emoji GIF (no download)"""
        return os.path.join(self.PATH, "assets", "emojis", f"{codepoint}.gif")

    def get_card_back_path(self) -> str:
        """Return path to card back image"""
        return os.path.join(self.PATH, "assets", "card_back.png")

    def get_random_emojis(self, count: int) -> list:
        """Select random emojis for a game (filtered for kids)"""
        if not self.emoji_index:
            log.error("No emoji index loaded!")
            return []

        # Filter out inappropriate emojis
        blocked_prefixes = [
            "1f595",  # middle finger
        ]

        available = []
        for e in self.emoji_index:
            codepoint = e["codepoint"]
            # Check if codepoint starts with any blocked prefix
            if not any(codepoint.startswith(prefix) for prefix in blocked_prefixes):
                available.append(codepoint)

        return random.sample(available, min(count, len(available)))

    def register_action(self, card_index: int, action):
        """Register a MemoryCard action instance"""
        self.game_state["actions"][card_index] = action

    def unregister_action(self, card_index: int):
        """Unregister a MemoryCard action instance"""
        if card_index in self.game_state["actions"]:
            del self.game_state["actions"][card_index]

    def get_action(self, card_index: int):
        """Get action instance by card index"""
        return self.game_state["actions"].get(card_index)

    def create_game_page(self, deck_controller) -> None:
        """Create a new game page with memory cards"""
        # Save current page for back navigation (only if not already on MemoryGame)
        current_page = deck_controller.active_page.json_path
        if not current_page.endswith("MemoryGame.json"):
            self.game_state["back_page"] = current_page
            log.info(f"Saved back_page: {current_page}")
        self.game_state["deck_controller"] = deck_controller

        # Get deck dimensions
        key_layout = deck_controller.deck.key_layout()
        rows, cols = key_layout[0], key_layout[1]

        log.info(f"Creating game for deck {rows}x{cols}")

        # Calculate number of pairs (reserve 1 slot for score/back)
        available_slots = rows * cols - 1
        num_pairs = available_slots // 2

        # Get random emojis for the game
        selected_emojis = self.get_random_emojis(num_pairs)
        cards = selected_emojis * 2  # Create pairs
        random.shuffle(cards)

        # Initialize game state
        self.game_state["cards"] = cards
        self.game_state["revealed"] = []
        self.game_state["matched"] = []
        self.game_state["first_card"] = None
        self.game_state["moves"] = 0
        self.game_state["start_time"] = time.time()
        self.game_state["game_active"] = True
        self.game_state["actions"] = {}

        # Build page dictionary
        page_dict = {"keys": {}}

        # Score display (with long-press back) at 0x0
        page_dict["keys"]["0x0"] = {
            "states": {
                "0": {
                    "actions": [{
                        "id": "com_pol_emoji_memory::ScoreDisplay",
                        "settings": {}
                    }],
                    "image-control-action": 0,
                    "label-control-actions": [0, 0, 0],
                    "background-control-action": 0,
                    "background": {"color": [50, 50, 80, 255]}
                }
            }
        }

        # Memory cards
        card_idx = 0
        for row in range(rows):
            for col in range(cols):
                # Skip score position
                if col == 0 and row == 0:
                    continue
                if card_idx >= len(cards):
                    break

                page_dict["keys"][f"{col}x{row}"] = {
                    "states": {
                        "0": {
                            "actions": [{
                                "id": "com_pol_emoji_memory::MemoryCard",
                                "settings": {"card_index": card_idx}
                            }],
                            "image-control-action": 0,
                            "label-control-actions": [0, 0, 0],
                            "background-control-action": 0,
                            "background": {"color": [60, 60, 100, 255]}
                        }
                    }
                }
                card_idx += 1

        # Create and load the page
        page_name = "MemoryGame"
        page_path = os.path.join(gl.DATA_PATH, "pages", f"{page_name}.json")

        log.info(f"Page dict: {page_dict}")
        log.info(f"Page path: {page_path}")

        # Save page to file first
        os.makedirs(os.path.dirname(page_path), exist_ok=True)
        with open(page_path, "w") as f:
            json.dump(page_dict, f, indent=2)

        # Load the page
        page = gl.page_manager.get_page(page_path, deck_controller)
        deck_controller.load_page(page)

        log.info(f"Game started with {num_pairs} pairs")

    def hide_cards(self, idx1: int, idx2: int) -> None:
        """Hide two cards after failed match"""
        state = self.game_state
        if not state["game_active"]:
            return

        # Remove from revealed
        if idx1 in state["revealed"]:
            state["revealed"].remove(idx1)
        if idx2 in state["revealed"]:
            state["revealed"].remove(idx2)

        # Update card displays
        action1 = self.get_action(idx1)
        action2 = self.get_action(idx2)

        if action1:
            action1.show_card_back()
        if action2:
            action2.show_card_back()

    def clear_matched_cards(self, idx1: int, idx2: int) -> None:
        """Clear matched cards from the board"""
        state = self.game_state
        if not state["game_active"]:
            return

        action1 = self.get_action(idx1)
        action2 = self.get_action(idx2)

        if action1:
            action1.show_matched()
        if action2:
            action2.show_matched()

    def show_victory(self) -> None:
        """Show victory message"""
        state = self.game_state
        elapsed = int(time.time() - state["start_time"])
        moves = state["moves"]

        log.info(f"Victory! {moves} moves in {elapsed}s")

        state["game_active"] = False

        # Update all cards to show victory state (green background)
        for card_index, action in list(state["actions"].items()):
            if hasattr(action, "show_victory"):
                action.show_victory()

        # Update score display to show final score
        if self.score_display_action:
            self.score_display_action.show_victory_score(moves, elapsed)

    def go_back(self, deck_controller) -> None:
        """Return to the previous page"""
        back_page = self.game_state.get("back_page")
        log.info(f"go_back called, back_page={back_page}")
        if back_page and os.path.exists(back_page):
            self.game_state["game_active"] = False
            page = gl.page_manager.get_page(back_page, deck_controller)
            deck_controller.load_page(page)
        else:
            log.warning(f"No back page available: {back_page}")
