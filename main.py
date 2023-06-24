import math
import json
from dataclasses import dataclass
from enum import Enum
import random

class WeaponType(Enum):
    MELEE = 1
    RANGE = 2


class DicePart:
    def __init__(self, val) -> None:
        self.random = False
        if "d" in val:
            self.random = True
        self.val = int(val.replace("d", ""))

    def get(self):
        if self.random:
            return random.randint(1, self.val)
        else:
            return self.val
    
    def prob(self):
        if self.random:
            return (self.val+1)/2
        else:
            return self.val
    
    def __str__(self) -> str:
        if self.random:
            return f"D{self.val}"
        else:
            return f"{self.val}"
    
    def __repr__(self) -> str:
        return self.__str__()

class Dice:
    def __init__(self, val) -> None:
        val = val.lower()
        self.base = None
        self.addition = None
        if "+" in val:
            splitted = val.split("+")
            self.base = DicePart(splitted[0])
            self.addition = DicePart(splitted[1])
        else:
            self.base = DicePart(val)
    
    def get(self):
        if self.addition:
            return self.base.get() + self.addition.get()
        else:
            return self.base.get()
    
    def prob(self):
        if self.addition:
            return self.base.prob() + self.addition.prob()
        else:
            return self.base.prob()
        
    def __str__(self) -> str:
        if self.addition:
            return f"{self.base}+{self.addition}"
        else:
            return f"{self.base}"     
    
    def __repr__(self) -> str:
        return self.__str__()


@dataclass
class Weapon:
    name: str
    keywords: list[str]
    attacks: Dice
    ap: int
    damage: Dice
    strength: int
    skill: int
    type: WeaponType # range or melee?

@dataclass
class Abilities:
    wargear: list
    core: list
    faction: list
    primarch: list
    invul: dict
    other: list
    special: list
    damaged: dict

@dataclass
class Unit:
    name: str
    movement: int
    wounds: int
    oc: int
    toughness: int
    leadership: int
    save: int
    weapons: list[Weapon]
    abilities: Abilities
    points: list


class Faction:
    def __init__(self, units: list[Unit]) -> None:
        self.units = units
    
    def get_unit_by_name(self, name):
        for u in self.units:
            if u.name == name:
                return u
        raise Exception(f"couldnt find {name}")
        

class Roll:
    def __init__(self, throws: int) -> None:
        self._throw(throws)


    def _throw(self, throws):
        self.dice = []
        for i in range(1,7):
            self.dice.append(throws*1/6)

    def roll(self, min):
        success = 0
        for i in range(len(self.dice)):
            if i+1 >= min: # i is 0-5, dice 1-6
                success += self.dice[i] 
        t = int(success)
        

        return success


def s_t(s, t):
    if s == t:
        return 4
    if s >= 2*t:
        return 2
    if 2*s <= t:
        return 6
    if s > t:
        return 3
    if s < t:
        return 5

def prob(d):
    if d < 1:
        return 1
    return (7-d)/6

class FightPair:
    def __init__(self, attacker: Unit, target: Unit) -> None:
        self.attacker = attacker
        self.target = target
    
    def attack(self, weapon):
        # TODO: keywords
        damage = weapon.attacks.prob() * prob(weapon.skill) * prob(s_t(weapon.strength, self.target.toughness)) * weapon.damage.prob() 
         
        invu = clean(self.target.abilities.invul["value"])
        saves = self.target.save + weapon.ap
        if invu and invu < saves:
            print(f"Using invu {invu}")
            damage = damage * 1-prob(invu)
        else:
            damage = damage * 1-prob(saves)
        return damage

    def attack_all_melee(self):
        print(f"{self.attacker.name} is attacking {self.target.name}.")
        for weapon in self.attacker.weapons:
            #print(weapon)
            if weapon.type == WeaponType.MELEE:
                damage = self.attack(weapon=weapon)
                print(f"Attacking with {weapon.name} deals {damage} on average.")



    #def attack_all_ranged(attacker: Unit, target: Unit):


def clean(t):
     if t == "N/A":
         return 1
     t = t.replace("+", "").replace('"', '').replace("-", "")
     if t == "":
         return 0
     return int(t)


def get_faction_by_id(id):
    loaded = json.load(open("data_exported_data.json", "r"))["keyvaluepairs"][0]

    for faction in loaded["data"]:
        if faction["id"] == id:
            break

    ds = faction["datasheets"]
    units = []
    for u in ds:
        ranged_weapons = u["rangedWeapons"]
        melee_weapons = u["meleeWeapons"]
        weapons = []
        for weapon in ranged_weapons:
            for profile in weapon["profiles"]:
                w = Weapon(name=profile["name"], 
                    keywords=profile["keywords"],
                    type=WeaponType.MELEE if profile["range"] == "Melee" else WeaponType.RANGE,
                    attacks=Dice(profile["attacks"]),
                    skill=clean(profile["skill"]),
                    strength=clean(profile["strength"]),
                    ap=clean(profile["ap"]),
                    damage=Dice(profile["damage"]))
                weapons.append(w)
        
        for weapon in melee_weapons:
            for profile in weapon["profiles"]:
                w = Weapon(name=profile["name"], 
                    keywords=profile["keywords"],
                    type=WeaponType.MELEE if profile["range"] == "Melee" else WeaponType.MELEE,
                    attacks=Dice(profile["attacks"]),
                    skill=clean(profile["skill"]),
                    strength=clean(profile["strength"]),
                    ap=clean(profile["ap"]),
                    damage=Dice(profile["damage"]))
                weapons.append(w)
        
        stats = u["stats"]
        if len(stats) == 0:
            continue
        s = stats[0]

        unit = Unit(name = s["name"],
        toughness = clean(s["t"]),
        movement = clean(s["m"]),
        save = clean(s["sv"]),
        wounds = clean(s["w"]),
        leadership = clean(s["ld"]),
        oc = clean(s["oc"]),
        abilities=Abilities(**u["abilities"]),
        points=u["points"],
        weapons=weapons)

        units.append(unit)

    return Faction(units)

f = get_faction_by_id("CSM")
terms = f.get_unit_by_name("Chaos Terminator Squad")
legionaires = f.get_unit_by_name("Chaos Terminator Squad")

fp = FightPair(attacker=terms, target=legionaires)
fp.attack_all_melee()