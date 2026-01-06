# gamemap.python
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Command:
    verb: str
    arg: Optional[str] = None


def parse_command(raw: str) ->Command:
  raw = raw.strip().lower()
  if not raw:
     return Command(verb="")

  parts: List[str] = raw.split()

  if len(parts) >= 3 and parts[0] =="talk" and parts[1] =="to":
    returnCommand(verb="talk", arg=" ".join(parts[2:]).strip() or None)

   return Command(
     verb=parts[0],
     arg=(" ".join(parts[1:]) if len(parts) > 1 else None) or None,
   )
