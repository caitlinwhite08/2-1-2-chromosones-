#Main Game Script
from engine import GameEngine
from parser import parse_command

def main():
try: 
    engine = GameEngine.load_from_file("game_map.json")
except FileNotFoundError:
    print("Error: game_map.json not found.")
    return
except GameDataError as e:
    print (f"Error in game_map.json{e}")
    return

print ("Text Adventure Engine (FrameWork Style)")
print ("Type HELP for commands")
#starts the On_enter events in the start room
start_events = engine.current_room().events.get("on_enter", [])
for m in engine.apply_events(start_events):
    print(m)
    print(engine.describe_current())
