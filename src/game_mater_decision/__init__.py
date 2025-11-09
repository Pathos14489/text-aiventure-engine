from typing import Union

from .spawn_character import SpawnCharacterDecision
from .spawn_item import SpawnItemDecision
from .spawn_new_location import SpawnNewLocationDecision
from .further_describe_current_location import FurtherDescribeCurrentLocationDecision
from .give_player_item import GivePlayerItemDecision
from .damage import DamageDecision
from .kill import KillDecision
from .equip_item import EquipItemDecision
from .unequip_item import UnequipItemDecision
from .drop_item import DropItemDecision
from .pick_up_item import PickUpItemDecision
from .teleport import TeleportDecision

SomeDecision = Union[TeleportDecision, SpawnCharacterDecision, SpawnItemDecision, SpawnNewLocationDecision, FurtherDescribeCurrentLocationDecision, GivePlayerItemDecision, DamageDecision, KillDecision, EquipItemDecision, UnequipItemDecision, DropItemDecision, PickUpItemDecision]