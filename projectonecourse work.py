#!/usr/bin/env python3
"""
Willow Manor Adventure - Text-Based Adventure Game

- Loads game world from JSON file (default: game_map.json)
- Supports navigation, inventory, items, locked doors, NPCs, save/load, win/lose conditions
- Complete adventure game featuring Willowbrook Manor

Usage:
    python willow_manor_adventure.py [path/to/game_map.json]

Game Features:
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
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

WILLOW_MANOR_GAME = {
    "metadata": {
        "title": "Willow Manor Adventure",
        "author": "Adventure Games Studio",
        "description": "A thrilling adventure through the mysterious Willowbrook Manor"
    },
    "rooms": {
        "Hall": {
            "description": "You stand in the grand entrance hall of Willowbrook Manor. Ornate pillars reach up to a vaulted ceiling painted with faded frescoes. A magnificent crystal chandelier hangs overhead, casting dancing shadows. To the east, warm light spills from the Kitchen doorway, while south leads to what appears to be a lush Garden through tall glass doors.",
            "items": ["dusty_map", "brass_key"],
            "exits": {
                "east": {"to": "Kitchen"},
                "south": {"to": "Garden"},
                "north": {"to": "Library", "locked": True, "key": "brass_key"},
                "west": {"to": "Storage Room", "locked": True, "key": "rusty_key"}
            },
            "tasks": ["Find the brass key to unlock the Library", "Explore all accessible rooms"]
        },
        "Kitchen": {
            "description": "A spacious Victorian kitchen with copper pots hanging from hooks and a large cast-iron stove dominating one wall. The smell of old spices lingers in the air. A sturdy wooden table sits in the center, scarred from years of meal preparation. There's a locked pantry to the north - you'll need the silver key to open it.",
            "items": ["sharp_knife", "silver_key", "cooking_pot", "old_recipe"],
            "exits": {
                "west": {"to": "Hall"},
                "north": {"to": "Treasure Room", "locked": True, "key": "silver_key"},
                "east": {"to": "Dining Room"}
            },
            "tasks": ["Collect cooking utensils", "Find the silver key to access the pantry"]
        },
        "Garden": {
            "description": "A beautiful but overgrown garden stretches before you. Rose bushes climb wild up trellises, and a stone fountain sits silent in the center, filled with fallen leaves. Ancient oak trees provide shade over weathered stone benches. The air is sweet with the scent of jasmine and lavender.",
            "items": ["beautiful_flower", "garden_shears", "watering_can"],
            "exits": {
                "north": {"to": "Hall"},
                "east": {"to": "Greenhouse"}
            },
            "npcs": {
                "old_gardener": {
                    "name": "Old Gardener", 
                    "dialogue": [
                        "Ah, a visitor! I've been tending these gardens for forty years...",
                        "The master's treasure is well hidden, they say. Look for the three golden coins.",
                        "That greenhouse to the east holds secrets - but beware the riddle within!",
                        "The rusty key you seek lies where books gather dust..."
                    ]
                }
            },
            "tasks": ["Talk to the Old Gardener for clues", "Gather gardening tools"]
        },
        "Library": {
            "description": "Floor-to-ceiling bookshelves line the walls of this magnificent library. Leather-bound volumes in various languages create a musty, scholarly atmosphere. A mahogany reading desk sits by a tall window, and a rolling ladder allows access to the highest shelves. Dust motes dance in streams of sunlight.",
            "items": ["ancient_book", "rusty_key", "magnifying_glass", "golden_coin"],
            "exits": {
                "south": {"to": "Hall"}
            },
            "npcs": {
                "ghost_librarian": {
                    "name": "Ghostly Librarian",
                    "dialogue": [
                        "Welcome to my eternal collection... *voice echoes*",
                        "Knowledge is the greatest treasure, but gold has its place too...",
                        "The greenhouse riddle speaks of what grows but is not alive...",
                        "Seek the crystal where light bends and wisdom hides..."
                    ]
                }
            },
            "tasks": ["Read the ancient book for clues", "Collect the golden coin", "Get the rusty key"]
        },
        "Storage Room": {
            "description": "A cluttered storage room filled with dusty furniture covered in white sheets, old paintings leaning against the walls, and wooden crates stacked high. Cobwebs drape the corners like nature's curtains. The air smells of old wood and forgotten memories.",
            "items": ["golden_coin", "old_painting", "wooden_crate", "crystal_prism"],
            "exits": {
                "east": {"to": "Hall"}
            },
            "tasks": ["Search through the stored items", "Find another golden coin"]
        },
        "Dining Room": {
            "description": "An elegant dining room with a long mahogany table set for twelve. Fine china and crystal glasses catch the light from a window overlooking the garden. Portraits of stern-faced ancestors watch from gilded frames on the walls.",
            "items": ["fine_china", "crystal_glass", "golden_coin"],
            "exits": {
                "west": {"to": "Kitchen"}
            },
            "tasks": ["Collect the third golden coin", "Examine the ancestor portraits"]
        },
        "Greenhouse": {
            "description": "A Victorian greenhouse filled with exotic plants and flowers. The glass ceiling allows dappled sunlight to filter through climbing vines. In the center stands an ornate pedestal with an inscription that reads: 'I am not alive, yet I grow; I have no lungs, yet I need air; I have no mouth, yet water kills me. What am I?'",
            "items": ["exotic_flower", "plant_seeds"],
            "exits": {
                "west": {"to": "Garden"}
            },
            "riddle": {
                "question": "I am not alive, yet I grow; I have no lungs, yet I need air; I have no mouth, yet water kills me. What am I?",
                "answer": "fire",
                "reward": "magic_fire_crystal",
                "solved": False
            },
            "tasks": ["Solve the riddle to get the magic crystal"]
        },
        "Treasure Room": {
            "description": "You've discovered the secret treasure room! Golden light reflects off precious gems scattered across ornate chests. Ancient coins glitter in piles, and mysterious artifacts line marble shelves. This is clearly the heart of Willowbrook Manor's legendary wealth.",
            "items": ["treasure_chest", "precious_gems", "ancient_artifact"],
            "exits": {
                "south": {"to": "Kitchen"}
            },
            "tasks": ["Claim your well-earned treasure!"]
        }
    },
    "start": "Hall",
    "win_condition": {
        "inventory_contains": ["golden_coin"],
        "inventory_count": {"golden_coin": 3},
        "has_solved_riddle": True
    },
    "lose_condition": None,
    "tasks": {
        "main_quest": "Collect all three golden coins and solve the greenhouse riddle to unlock the manor's greatest secret!",
        "side_quests": [
            "Talk to all NPCs to learn the manor's history",
            "Collect all the kitchen utensils",
            "Gather gardening tools from the garden",
            "Read the ancient book in the library",
            "Examine all the ancestor portraits"
        ]
    }
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
        self.completed_tasks: List[str] = []
        self.riddles_solved: Dict[str, bool] = {}
        self.hints_given: int = 0

        # Basic validation
        if self.current is None or self.current not in self.rooms:
            raise RuntimeError("Game must contain a valid 'start' room present in 'rooms'.")

    def show_instructions(self) -> None:
        """Display comprehensive game instructions."""
        print("=" * 70)
        print("                   WELCOME TO WILLOW MANOR!")
        print("=" * 70)
        print()
        meta = self.map.get("metadata", {})
        print(f"🏰 {meta.get('title', 'Willow Manor Adventure')}")
        if meta.get("author"):
            print(f"📚 By: {meta.get('author')}")
        if meta.get("description"):
            print(f"📖 {meta.get('description')}")
        print()
        
        tasks = self.map.get("tasks", {})
        if tasks.get("main_quest"):
            print("🎯 MAIN QUEST:")
            print(f"   {tasks['main_quest']}")
            print()
        
        print("🎮 HOW TO PLAY:")
        print("   • Explore rooms by moving in different directions")
        print("   • Collect items that might be useful on your quest")
        print("   • Talk to NPCs (Non-Player Characters) for clues and story")
        print("   • Solve puzzles and riddles to progress")
        print("   • Complete tasks to advance your adventure")
        print()
        print("💡 HELPFUL COMMANDS:")
        print("   Movement: 'north', 'n', 'go east', 'south', etc.")
        print("   Items: 'take knife', 'drop flower', 'inventory'")
        print("   Interaction: 'look', 'talk gardener', 'examine book'")
        print("   Riddles: 'answer fire' (when solving riddles)")
        print("   Help: 'hint' (get a helpful tip), 'tasks' (see objectives)")
        print("   Game: 'save', 'load', 'help', 'quit'")
        print()
        print("🔍 TIPS FOR SUCCESS:")
        print("   • Read room descriptions carefully - they contain clues!")
        print("   • Talk to everyone you meet - NPCs have valuable information")
        print("   • Some doors are locked - find the right keys!")
        print("   • Keep track of your tasks with the 'tasks' command")
        print("   • Use 'hint' if you get stuck (up to 3 hints available)")
        print("   • Save your game regularly!")
        print()
        print("=" * 70)
        print()
        input("Press Enter to begin your adventure... 🚀")
        print()

    # ------------------ Persistence ------------------
    def save_game(self, filename: str) -> None:
        """Save the player's current state to a JSON file."""
        payload = {
            "current": self.current,
            "inventory": self.inventory,
            "npc_progress": self.npc_progress,
            "completed_tasks": self.completed_tasks,
            "riddles_solved": self.riddles_solved,
            "hints_given": self.hints_given
        }
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print(f"💾 Game saved to '{filename}'.")
        except OSError as e:
            print(f"❌ Error saving game: {e}")

    def load_game(self, filename: str) -> None:
        """Load previously saved state."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current = data.get("current", self.current)
            self.inventory = data.get("inventory", self.inventory)
            self.npc_progress = data.get("npc_progress", self.npc_progress)
            self.completed_tasks = data.get("completed_tasks", self.completed_tasks)
            self.riddles_solved = data.get("riddles_solved", self.riddles_solved)
            self.hints_given = data.get("hints_given", self.hints_given)
            print(f"📁 Game loaded from '{filename}'.")
            self.look()
            self.check_conditions()
        except FileNotFoundError:
            print(f"❌ No save file found at '{filename}'.")
        except json.JSONDecodeError:
            print("❌ Save file is corrupted.")
        except OSError as e:
            print(f"❌ Error loading save: {e}")

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

    def count_item_in_inventory(self, item_name: str) -> int:
        """Count how many of a specific item the player has."""
        return sum(1 for item in self.inventory if item.lower() == item_name.lower())

    def look(self) -> None:
        """Describe the current room, items, NPCs, and exits."""
        room = self.current_room()
        print(f"\n🏛️  == {self.current} ==")
        print(room.get("description", ""))
        
        items = room.get("items", [])
        if items:
            print(f"\n📦 You see: {', '.join(items)}")
        
        npcs = room.get("npcs", {})
        if npcs:
            names = [v.get("name", k) for k, v in npcs.items()]
            print(f"\n👥 People here: {', '.join(names)}")
        
        # Check for riddles
        if "riddle" in room and not room["riddle"].get("solved", False):
            print(f"\n🧩 There's a riddle here: {room['riddle']['question']}")
        
        exits = room.get("exits", {})
        if exits:
            formatted = []
            for direction, meta in exits.items():
                label = direction
                if meta.get("locked"):
                    label += " (🔒 locked)"
                formatted.append(label)
            print(f"\n🚪 Exits: {', '.join(formatted)}")
        
        # Show room tasks
        tasks = room.get("tasks", [])
        if tasks:
            print(f"\n✅ Tasks here: {', '.join(tasks)}")
        
        print()

    def show_inventory(self) -> None:
        if self.inventory:
            # Group identical items and show counts
            item_counts = {}
            for item in self.inventory:
                item_counts[item] = item_counts.get(item, 0) + 1
            
            inventory_display = []
            for item, count in item_counts.items():
                if count > 1:
                    inventory_display.append(f"{item} (x{count})")
                else:
                    inventory_display.append(item)
            
            print(f"🎒 You are carrying: {', '.join(inventory_display)}")
        else:
            print("🎒 You are not carrying anything.")

    def show_tasks(self) -> None:
        """Display current tasks and progress."""
        print("\n📋 === CURRENT TASKS ===")
        
        tasks = self.map.get("tasks", {})
        if tasks.get("main_quest"):
            print(f"🎯 MAIN QUEST: {tasks['main_quest']}")
        
        print("\n📝 ROOM TASKS:")
        all_tasks = []
        for room_name, room_data in self.rooms.items():
            room_tasks = room_data.get("tasks", [])
            for task in room_tasks:
                status = "✅" if task in self.completed_tasks else "⭕"
                all_tasks.append(f"  {status} {task} (in {room_name})")
        
        if all_tasks:
            print("\n".join(all_tasks))
        
        if tasks.get("side_quests"):
            print("\n🌟 SIDE QUESTS:")
            for quest in tasks["side_quests"]:
                status = "✅" if quest in self.completed_tasks else "⭕"
                print(f"  {status} {quest}")
        
        print(f"\n📊 Progress: {len(self.completed_tasks)} tasks completed")
        print()

    def give_hint(self) -> None:
        """Provide helpful hints to the player."""
        if self.hints_given >= 3:
            print("💡 You've used all your hints! Try exploring and talking to NPCs for more clues.")
            return
        
        hints = [
            "🔍 Start by exploring all the rooms you can access and talking to every NPC you meet.",
            "🗝️ Look for keys in rooms - they often unlock new areas. Check the Library for a rusty key!",
            "🪙 You need to collect three golden coins. Check the Library, Storage Room, and Dining Room.",
            "🔥 The greenhouse riddle asks about something that grows but isn't alive, needs air but has no lungs, and is killed by water. Think about what this could be!",
            "📚 The ancient book in the Library and conversations with NPCs contain important clues.",
        ]
        
        if self.hints_given < len(hints):
            print(f"💡 HINT #{self.hints_given + 1}: {hints[self.hints_given]}")
            self.hints_given += 1
        else:
            print("💡 You've received all available hints! Good luck with your adventure!")

    # ------------------ Player actions ------------------
    def go(self, direction: str) -> None:
        d = self.normalize_direction(direction)
        room = self.current_room()
        exits = room.get("exits", {})
        if d not in exits:
            print("🚫 You can't go that way.")
            return
        meta = exits[d]
        if meta.get("locked"):
            required_key = meta.get("key")
            # allow using a matching key automatically if present
            if required_key and self.find_case_insensitive(required_key, self.inventory):
                print(f"🗝️ You use the {required_key} to unlock the way {d}.")
                meta["locked"] = False
            else:
                print(f"🔒 The way is locked. You need a {required_key} to proceed.")
                return
        dest = meta.get("to")
        if not dest or dest not in self.rooms:
            print("🌫️ The exit seems to lead nowhere.")
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
            print(f"✅ You take the {found}.")
            
            # Check if this completes any tasks
            self.check_task_completion(f"collect {found}")
            self.check_conditions()
        else:
            print(f"❌ There is no '{item_name}' here.")

    def drop(self, item_name: str) -> None:
        found = self.find_case_insensitive(item_name, self.inventory)
        if found:
            self.inventory.remove(found)
            room = self.current_room()
            room.setdefault("items", []).append(found)
            print(f"📤 You drop the {found}.")
        else:
            print(f"❌ You don't have '{item_name}'.")

    def use(self, item_name: str, target: Optional[str] = None) -> None:
        found = self.find_case_insensitive(item_name, self.inventory)
        if not found:
            print(f"❌ You don't have '{item_name}'.")
            return
        # If using on a direction, try unlock
        if target:
            d = self.normalize_direction(target)
            room = self.current_room()
            exits = room.get("exits", {})
            if d not in exits:
                print("❌ There's no exit in that direction.")
                return
            meta = exits[d]
            if not meta.get("locked"):
                print("ℹ️ That way is already unlocked.")
                return
            required_key = meta.get("key")
            # case-insensitive compare
            if required_key and required_key.lower() == found.lower():
                meta["locked"] = False
                print(f"🗝️ You used the {found} to unlock the way {d}.")
                return
            else:
                print("❌ That key doesn't fit this lock.")
                return
        # Generic use
        print(f"🤷 You use the {found}, but nothing obvious happens.")

    def examine(self, item_name: str) -> None:
        """Examine items for more detailed descriptions."""
        # Check inventory first
        found = self.find_case_insensitive(item_name, self.inventory)
        if found:
            descriptions = {
                "dusty_map": "An old map of the manor showing secret passages and hidden rooms.",
                "ancient_book": "A leather-bound tome titled 'Secrets of Willowbrook Manor' - it mentions three golden coins hidden throughout the house.",
                "crystal_prism": "A beautiful crystal that refracts light into rainbow patterns. It seems to have magical properties.",
                "old_recipe": "A faded recipe for 'Treasure Hunter's Stew' - it lists unusual ingredients.",
                "magic_fire_crystal": "A warm, glowing crystal that pulses with inner fire. This is clearly magical!"
            }
            desc = descriptions.get(found, f"A {found.replace('_', ' ')}. Nothing particularly special about it.")
            print(f"🔍 {desc}")
            return
        
        # Check room items
        room = self.current_room()
        items = room.get("items", [])
        found = self.find_case_insensitive(item_name, items)
        if found:
            print(f"🔍 You see a {found.replace('_', ' ')} here. You could take it if you want.")
            return
        
        print(f"❌ You don't see any '{item_name}' to examine.")

    def answer(self, answer: str) -> None:
        """Answer riddles in the current room."""
        room = self.current_room()
        if "riddle" not in room:
            print("❌ There's no riddle to answer here.")
            return
        
        riddle = room["riddle"]
        if riddle.get("solved", False):
            print("✅ You've already solved this riddle!")
            return
        
        if answer.lower() == riddle["answer"].lower():
            print(f"🎉 Correct! The answer is '{riddle['answer']}'!")
            riddle["solved"] = True
            self.riddles_solved[self.current] = True
            
            # Give reward
            reward = riddle.get("reward")
            if reward:
                self.inventory.append(reward)
                print(f"🎁 You receive: {reward}!")
            
            self.check_task_completion("solve riddle")
            self.check_conditions()
        else:
            print(f"❌ '{answer}' is not correct. Think more carefully about the riddle!")

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
            print("❌ There's no one here by that name.")
            return
        npc = npcs[target_key]
        dialogue: List[str] = npc.get("dialogue", [])
        progress_key = f"{self.current}:{target_key}"
        progress = self.npc_progress.get(progress_key, 0)
        if not dialogue:
            print(f"😶 {npc.get('name', target_key)} has nothing to say.")
            return
        # speak current line, then advance (but don't go past last)
        line = dialogue[min(progress, len(dialogue) - 1)]
        print(f"💬 {npc.get('name', target_key)} says: \"{line}\"")
        if progress < len(dialogue) - 1:
            self.npc_progress[progress_key] = progress + 1
        
        # Check if talking completes any tasks
        self.check_task_completion(f"talk to {npc.get('name', target_key)}")

    def check_task_completion(self, action: str) -> None:
        """Check if an action completes any tasks."""
        # This is a simple task completion system
        # In a more complex game, you'd have more sophisticated task tracking
        pass

    # ------------------ Win/Lose Conditions ------------------
    def check_conditions(self) -> None:
        """Check win/lose conditions defined in the map and stop the game if met."""
        wc = self.map.get("win_condition")
        lc = self.map.get("lose_condition")
        if wc and self._evaluate_condition(wc):
            print("\n🎉 ===== CONGRATULATIONS! =====")
            print("🏆 You have successfully completed your quest!")
            print("💰 You've discovered the secrets of Willowbrook Manor!")
            print("🌟 The treasure and glory are yours!")
            print("==============================")
            self.is_running = False
            return
        if lc and self._evaluate_condition(lc):
            print("\n💀 You have met a lose condition. Game over.")
            self.is_running = False
            return

    def _evaluate_condition(self, cond: Dict[str, Any]) -> bool:
        """Evaluate condition objects supported by the engine."""
        if not cond:
            return False
        
        # Check all conditions must be met (AND logic)
        conditions_met = 0
        total_conditions = 0
        
        # inventory_contains: all listed items must be in player's inventory
        if "inventory_contains" in cond:
            total_conditions += 1
            required = cond["inventory_contains"]
            if all(self.find_case_insensitive(item, self.inventory) for item in required):
                conditions_met += 1
        
        # inventory_count: specific counts of items
        if "inventory_count" in cond:
            total_conditions += 1
            counts = cond["inventory_count"]
            if all(self.count_item_in_inventory(item) >= count for item, count in counts.items()):
                conditions_met += 1
        
        # has_solved_riddle: player has solved at least one riddle
        if "has_solved_riddle" in cond:
            total_conditions += 1
            if cond["has_solved_riddle"] and any(self.riddles_solved.values()):
                conditions_met += 1
        
        # inventory_has_any: player has any of the listed items
        if "inventory_has_any" in cond:
            total_conditions += 1
            options = cond["inventory_has_any"]
            if any(self.find_case_insensitive(item, self.inventory) for item in options):
                conditions_met += 1
        
        # in_room_equals: player is in specific room
        if "in_room_equals" in cond:
            total_conditions += 1
            if self.current == cond["in_room_equals"]:
                conditions_met += 1
        
        return conditions_met == total_conditions

    # ------------------ Command processing ------------------
    def parse_and_run(self, line: str) -> None:
        parts = line.strip().split()
        if not parts:
            return
        verb = parts[0].lower()
        args = parts[1:]

        # Single-word synonyms mapping
        if verb in ("quit", "exit"):
            print("👋 Goodbye! Thanks for playing Willow Manor Adventure!")
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
        if verb in ("tasks", "task", "quest", "quests"):
            self.show_tasks()
            return
        if verb in ("hint", "hints", "clue"):
            self.give_hint()
            return

        # Movement: 'go north' or just 'north'
        if verb in ("go", "move"):
            if not args:
                print("🤔 Go where?")
                return
            self.go(args[0])
            return
        if verb in ("north", "south", "east", "west", "up", "down",
                    "n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw"):
            self.go(verb)
            return

        # take / get
        if verb in ("take", "get", "pick", "grab"):
            if not args:
                print("🤔 Take what?")
                return
            self.take(" ".join(args))
            return

        # drop / leave
        if verb in ("drop", "leave", "put"):
            if not args:
                print("🤔 Drop what?")
                return
            self.drop(" ".join(args))
            return

        # examine
        if verb in ("examine", "inspect", "check", "read"):
            if not args:
                print("🤔 Examine what?")
                return
            self.examine(" ".join(args))
            return

        # answer (for riddles)
        if verb in ("answer", "solve"):
            if not args:
                print("🤔 Answer what?")
                return
            self.answer(" ".join(args))
            return

        # use <item> [on <target>]
        if verb == "use":
            if not args:
                print("🤔 Use what?")
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
        if verb in ("talk", "speak", "chat"):
            # allow "talk to old man" or "talk old man"
            if args and args[0].lower() == "to":
                args = args[1:]
            if not args:
                print("🤔 Talk to whom?")
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

        print("❓ I don't understand that command. Type 'help' for a list of commands.")

    def print_help(self) -> None:
        print(
            """
🎮 === WILLOW MANOR ADVENTURE COMMANDS ===
  
📍 MOVEMENT:
  go <direction> / <direction>  - Move (north, south, east, west, etc)
  n, s, e, w                   - Quick directional shortcuts

🎒 ITEMS:
  take <item>                  - Pick up an item
  drop <item>                  - Drop an item
  inventory / i                - Show your inventory
  examine <item>               - Get detailed info about an item
  use <item> [on <target>]     - Use an item

🗣️ INTERACTION:
  look / l                     - Describe current room
  talk <character>             - Speak with NPCs
  answer <solution>            - Answer riddles

📋 QUEST MANAGEMENT:
  tasks                        - Show current tasks and progress  
  hint                         - Get a helpful tip (3 available)

💾 GAME MANAGEMENT:
  save [filename]              - Save your progress
  load [filename]              - Load saved game
  help                         - Show this help
  quit / exit                  - Exit the game

💡 Remember: Explore thoroughly, talk to everyone, and read item descriptions!
"""
        )


# ------------------ Game loading / helper functions ------------------
def ensure_game_file(path: Path) -> Path:
    """Return a valid game file path; create Willow Manor Adventure if missing."""
    if path.exists():
        return path
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(WILLOW_MANOR_GAME, f, indent=2)
        print(f"🏰 Welcome to Willow Manor Adventure! Game file created at '{path}'.")
        print("🎮 You can edit this file to create your own custom adventures!")
    except OSError as e:
        print(f"❌ Unable to create game file: {e}")
        raise
    return path


def load_map(path: Path) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # basic validation
        if "rooms" not in data or not isinstance(data["rooms"], dict):
            print("❌ Game file missing 'rooms' dictionary.")
            sys.exit(1)
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Game file is not valid JSON: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"❌ Unable to read game file: {e}")
        sys.exit(1)


def main(argv: List[str]) -> None:
    map_path = Path(argv[1]) if len(argv) > 1 else Path("game_map.json")
    map_path = ensure_game_file(map_path)
    game_map = load_map(map_path)

    try:
        engine = GameEngine(game_map)
    except RuntimeError as e:
        print(f"❌ Game error: {e}")
        sys.exit(1)

    # Show instructions before starting
    engine.show_instructions()
    
    # Start the game
    engine.look()

    while engine.is_running:
        try:
            user_input = input("🎯 > ")
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye! Thanks for playing Willow Manor Adventure!")
            break
        engine.parse_and_run(user_input)


if __name__ == "__main__":
    main(sys.argv)