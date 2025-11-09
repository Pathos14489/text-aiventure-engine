from typing import Union

from .action import ActionDecision
from .attack import AttackDecision
from .drop import DropDecision
from .equip import EquipDecision
from .say import SayDecision
from .take import TakeDecision
from .unequip import UnequipDecision

SomeDecision = Union[ActionDecision, AttackDecision, DropDecision, EquipDecision, SayDecision, TakeDecision, UnequipDecision]