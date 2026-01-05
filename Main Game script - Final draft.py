from engine import GameEngine, GameDataError
from parser import parse_command 

def main():
    try:
        engine = GameEngine.load_from_file("game_map.json")
    except FileNotFoundError:
        print("Error: game_map.json not found.")
        return
    except GameDataError as e:
        print(f"Error in game_map.json:{e}")
        return
print("Text Adventure Engine (FrameWork Style)")
print("Type HELP for commands")

#Starts the On_enter events
start_events = engine.current_room().events.get("on_enter,[]")
for message in engine.apply_events(start_events):
    print(message)

#explains the room after events
print(engine.describe_current())

if __name__ == "__main__":
    main()
