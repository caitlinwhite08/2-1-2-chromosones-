#!/usr/bin/env python3
"""
Text-Based Adventure Game Engine

- Loads game world from JSON file (default: game_map.json)
- Supports navigation, inventory, items, locked doors, NPCs, save/load, win/lose conditions
- If game_map.json not found, creates a sample game map you can edit.

Usage:
    python text_adventure_engine.py [path/to/game_map.json]

Engine responsibilities:
- Load/validate the JSON world file
- Maintain player state (current room, inventory)
- Parse simple natural commands (verbs + nouns)
- Enforce locked exits, NPC dialogue, win/lose checks
- Save/load player state to a save file
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SAMPLE_GAME = {
    "rooms": {
        "Hall": {
            "description": "You are standing in a long hall. A door leads east to the Kitchen and south to the Garden.",
            "items": ["map"],
            "exits": {
                "east": {"to": "Kitchen"},
                "south": {"to": "Garden"}
            }
        },
        "Kitchen": {
            "description": "A tidy kitchen with a faint smell of spice. There's a locked door to the north.",
            "items": ["knife", "silver_key"],
            "exits": {
                "west": {"to": "Hall"},
                "north": {"to": "Treasure Room", "locked": True, "key": "silver_key"}
            }
        },
        "Garden": {
            "description": "A small garden. The flowers are in bloom.",
            "items": ["flower"],
            "exits": {
                "north": {"to": "Hall"}
            },
            "npcs": {
                "old_man": {"name": "Old Man", "dialogue": ["Stay awhile and listen...", "The treasure lies behind the locked door."]}
            }
        },
        "Treasure Room": {
            "description": "You've found the treasure room! A glittering chest sits in the centre.",
            "items": ["treasure"],
            "exits": {
                "south": {"to": "Kitchen"}
            }
        }
    },
    "start": "Hall",
    "win_condition": {"inventory_contains": ["treasure"]},
    "lose_condition": None,

}


# Direction aliases (allow 'n', 's', 'e', 'w' etc.)
DIRECTION_ALIASES = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down",
    "ne": "northeast",
    "nw": "northwest",
    "se": "southeast",
    "sw": "southwest",
}


class GameEngine:
    def __init__(self, map_data: Dict[str, Any]) -> None:
        self.map = map_data
        self.rooms: Dict[str, Dict[str, Any]] = self.map.get("rooms", {})
        self.current: Optional[str] = self.map.get("start")
        self.inventory: List[str] = []
        self.is_running: bool = True
        self.npc_progress: Dict[str, int] = {}

        # Basic validation
        if self.current is None or self.current not in self.rooms:
            raise RuntimeError("Map must contain a valid 'start' room present in 'rooms'.")

    # ------------------ Persistence ------------------
    def save_game(self, filename: str) -> None:
        """Save the player's current state to a JSON file."""
        payload = {
            "current": self.current,
            "inventory": self.inventory,
            "npc_progress": self.npc_progress,
        }
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"Game saved to '{filename}'.")
        except OSError as e:
            print(f"Error saving game: {e}")

    def load_game(self, filename: str) -> None:
        """Load previously saved state (current room, inventory, npc progress)."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current = data.get("current", self.current)
            self.inventory = data.get("inventory", self.inventory)
            self.npc_progress = data.get("npc_progress", self.npc_progress)
            print(f"Game loaded from '{filename}'.")
            self.look()
            self.check_conditions()
        except FileNotFoundError:
            print(f"No save file found at '{filename}'.")
        except json.JSONDecodeError:
            print("Save file is corrupted.")
        except OSError as e:
            print(f"Error loading save: {e}")

    # ------------------ Helpers ------------------
    def current_room(self) -> Dict[str, Any]:
        if self.current is None:
            raise RuntimeError("No current room set.")
        room = self.rooms.get(self.current)
        if room is None:
            raise RuntimeError(f"Current room '{self.current}' not defined.")
        return room

    def normalize_direction(self, d: str) -> str:
        d = d.lower()
        return DIRECTION_ALIASES.get(d, d)

    def find_case_insensitive(self, target: str, collection: List[str]) -> Optional[str]:
        """Find an exact match in collection, case-insensitive; return the actual item string or None."""
        target_lower = target.lower()
        for item in collection:
            if item.lower() == target_lower:
                return item
        return None

    def look(self) -> None:
        """Describe the current room, items, NPCs, and exits."""
        room = self.current_room()
        print(f"\n== {self.current} ==")
        print(room.get("description", ""))
        items = room.get("items", [])
        if items:
            print("You see:", ", ".join(items))
        npcs = room.get("npcs", {})
        if npcs:
            names = [v.get("name", k) for k, v in npcs.items()]
            print("People here:", ", ".join(names))
        exits = room.get("exits", {})
        if exits:
            formatted = []
            for direction, meta in exits.items():
                label = direction
                if meta.get("locked"):
                    label += " (locked)"
                formatted.append(label)
            print("Exits:", ", ".join(formatted))
        print()

    def show_inventory(self) -> None:
        if self.inventory:
            print("You are carrying:", ", ".join(self.inventory))
        else:
            print("You are not carrying anything.")

    # ------------------ Player actions ------------------
    def go(self, direction: str) -> None:
        d = self.normalize_direction(direction)
        room = self.current_room()
        exits = room.get("exits", {})
        if d not in exits:
            print("You can't go that way.")
            return
        meta = exits[d]
        if meta.get("locked"):
            required_key = meta.get("key")
            # allow using a matching key automatically if present
            if required_key and self.find_case_insensitive(required_key, self.inventory):
                print(f"You use the {required_key} to unlock the way {d}.")
                meta["locked"] = False
            else:
                print("The way is locked.")
                return
        dest = meta.get("to")
        if not dest or dest not in self.rooms:
            print("The exit seems to lead nowhere.")
            return
        self.current = dest
        self.look()
        self.check_conditions()

    def take(self, item_name: str) -> None:
        room = self.current_room()
        items = room.get("items", [])
        found = self.find_case_insensitive(item_name, items)
        if found:
            items.remove(found)
            self.inventory.append(found)
            print(f"You take the {found}.")
            self.check_conditions()
        else:
            print(f"There is no '{item_name}' here.")

    def drop(self, item_name: str) -> None:
        found = self.find_case_insensitive(item_name, self.inventory)
        if found:
            self.inventory.remove(found)
            room = self.current_room()
            room.setdefault("items", []).append(found)
            print(f"You drop the {found}.")
        else:
            print(f"You don't have '{item_name}'.")

    def use(self, item_name: str, target: Optional[str] = None) -> None:
        found = self.find_case_insensitive(item_name, self.inventory)
        if not found:
            print(f"You don't have '{item_name}'.")
            return
        # If using on a direction, try unlock
        if target:
            d = self.normalize_direction(target)
            room = self.current_room()
            exits = room.get("exits", {})
            if d not in exits:
                print("There's no exit in that direction.")
                return
            meta = exits[d]
            if not meta.get("locked"):
                print("That way is already unlocked.")
                return
            required_key = meta.get("key")
            # case-insensitive compare
            if required_key and required_key.lower() == found.lower():
                meta["locked"] = False
                print(f"You used the {found} to unlock the way {d}.")
                return
            else:
                print("That key doesn't fit this lock.")
                return
        # Generic use
        print(f"You use the {found}, but nothing obvious happens.")

    def talk(self, npc_key_or_name: str) -> None:
        room = self.current_room()
        npcs: Dict[str, Dict[str, Any]] = room.get("npcs", {})
        target_key = None
        for key, data in npcs.items():
            display = data.get("name", key)
            if key.lower() == npc_key_or_name.lower() or display.lower() == npc_key_or_name.lower():
                target_key = key
                break
        if not target_key:
            print("There's no one here by that name.")
            return
        npc = npcs[target_key]
        dialogue: List[str] = npc.get("dialogue", [])
        progress_key = f"{self.current}:{target_key}"
        progress = self.npc_progress.get(progress_key, 0)
        if not dialogue:
            print(f"{npc.get('name', target_key)} has nothing to say.")
            return
        # speak current line, then advance (but don't go past last)
        line = dialogue[min(progress, len(dialogue) - 1)]
        print(f"{npc.get('name', target_key)} says: \"{line}\"")
        if progress < len(dialogue) - 1:
            self.npc_progress[progress_key] = progress + 1

    # ------------------ Win/Lose Conditions ------------------
    def check_conditions(self) -> None:
        """Check win/lose conditions defined in the map and stop the game if met."""
        wc = self.map.get("win_condition")
        lc = self.map.get("lose_condition")
        if wc and self._evaluate_condition(wc):
            print("\nCONGRATULATIONS! You've met the win condition.")
            self.is_running = False
            return
        if lc and self._evaluate_condition(lc):
            print("\nYou have met a lose condition. Game over.")
            self.is_running = False
            return

    def _evaluate_condition(self, cond: Dict[str, Any]) -> bool:
        """Evaluate condition objects supported by the engine."""
        if not cond:
            return False
        # inventory_contains: all listed items must be in player's inventory
        if "inventory_contains" in cond:
            required = cond["inventory_contains"]
            return all(self.find_case_insensitive(item, self.inventory) for item in required)
        if "inventory_has_any" in cond:
            options = cond["inventory_has_any"]
            return any(self.find_case_insensitive(item, self.inventory) for item in options)
        if "in_room_equals" in cond:
            return self.current == cond["in_room_equals"]
        # Unknown condition -> false
        return False

    # ------------------ Command processing ------------------
    def parse_and_run(self, line: str) -> None:
        parts = line.strip().split()
        if not parts:
            return
        verb = parts[0].lower()
        args = parts[1:]

        # Single-word synonyms mapping
        if verb in ("quit", "exit"):
            print("Goodbye.")
            self.is_running = False
            return
        if verb in ("look", "l"):
            self.look()
            return
        if verb in ("inventory", "i"):
            self.show_inventory()
            return
        if verb in ("help", "?"):
            self.print_help()
            return

        # Movement: 'go north' or just 'north'
        if verb in ("go", "move"):
            if not args:
                print("Go where?")
                return
            self.go(args[0])
            return
        if verb in ("north", "south", "east", "west", "up", "down",
                    "n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw"):
            self.go(verb)
            return

        # take / get
        if verb in ("take", "get", "pick"):
            if not args:
                print("Take what?")
                return
            self.take(" ".join(args))
            return

        # drop / leave
        if verb in ("drop", "leave"):
            if not args:
                print("Drop what?")
                return
            self.drop(" ".join(args))
            return

        # use <item> [on <target>]
        if verb == "use":
            if not args:
                print("Use what?")
                return
            # parse optional 'on'
            if "on" in args:
                idx = args.index("on")
                item = " ".join(args[:idx])
                target = " ".join(args[idx + 1 :]) if idx + 1 < len(args) else None
            else:
                item = args[0]
                target = " ".join(args[1:]) if len(args) > 1 else None
            self.use(item, target)
            return

        # talk to <npc>
        if verb in ("talk", "speak"):
            # allow "talk to old man" or "talk old man"
            if args and args[0].lower() == "to":
                args = args[1:]
            if not args:
                print("Talk to whom?")
                return
            self.talk(" ".join(args))
            return

        # save/load
        if verb == "save":
            fname = args[0] if args else "save.json"
            self.save_game(fname)
            return
        if verb == "load":
            fname = args[0] if args else "save.json"
            self.load_game(fname)
            return

        print("I don't understand that command. Type 'help' for a list of commands.")

    def print_help(self) -> None:
        print(
            """
Commands:
  look or l                   - Describe the current room
  go <direction>              - Move (north, south, east, west, etc)
  <direction>                 - Shortcut to move (north, n, south, s, etc)
  take <item>                 - Pick up an item
  drop <item>                 - Drop an item
  inventory or i              - Show your inventory
  use <item> [on <target>]    - Use an item (e.g., use silver_key on north)
  talk <npc>                  - Talk to an NPC
  save [filename]             - Save your game (default: save.json)
  load [filename]             - Load a saved game (default: save.json)
  quit / exit                 - Exit the game
  help                        - Show this help
"""
        )


# ------------------ Map loading / helper functions ------------------
def ensure_map_file(path: Path) -> Path:
    """Return a valid map file path; create a sample if missing."""
    if path.exists():
        return path
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_GAME, f, indent=2)
        print(f"No map found. Created sample map at '{path}'. Edit it to make your own game.")
    except OSError as e:
        print(f"Unable to create sample map file: {e}")
        raise
    return path


def load_map(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # basic validation
        if "rooms" not in data or not isinstance(data["rooms"], dict):
            print("Map file missing 'rooms' dictionary.")
            sys.exit(1)
        return data
    except json.JSONDecodeError as e:
        print(f"Map file is not valid JSON: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"Unable to read map file: {e}")
        sys.exit(1)


def main(argv: List[str]) -> None:
    map_path = Path(argv[1]) if len(argv) > 1 else Path("game_map.json")
    map_path = ensure_map_file(map_path)
    game_map = load_map(map_path)

    try:
        engine = GameEngine(game_map)
    except RuntimeError as e:
        print(f"Map error: {e}")
        sys.exit(1)

    meta = game_map.get("metadata", {})
    title = meta.get("title", "Text Adventure")
    author = meta.get("author", "")
    print(f"\n{title} by {author}\nType 'help' for commands.\n")

    engine.look()

    while engine.is_running:
        try:
            user_input = input("> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        engine.parse_and_run(user_input)


if __name__ == "__main__":
    main(sys.argv)