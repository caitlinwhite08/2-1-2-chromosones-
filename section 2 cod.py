class GameEngine:
    def_init_(self,rooms.npcs,rules,start_room)->None:
      self.rooms=rooms
      self.npcs=npcs
      self.rules=rules
      self.state=GameState(current_room=start_room,inventory=[])

      self.commands={
      "help":self.cmd_help,
      "look":self.cmd_look,
      "inventory":self,cmd_inventory,
      "tasks":self.cmd_tasks,
      "go":self.cmd_go,
      "get":self.cmd_get,
      "drop":self.cmd_drop,
      "use":self.cmd_use,
      "talk":self.cmd_talk,
      "save":self.cmd_save,
      "load":self.cmd_load
      "quit":self.cmd_quit,
      }
      self._should_quit=False

      @staticmethod
      def load_from_file(path:str)->"GameEngine":
        ...
        return GameEngine(...)
