#

#

# **Spellcasters Chronicles: Game Mechanics & Logic Master**

## **0\.Technical Artifact: Domain Model Specification**

A declarative Domain Model Specification serving as the "Single Source of Truth" for the _Spellcasters Chronicles_ application state. It defines the entities, attributes, relationships, and invariant rules required to generate a strict JSON Schema (Draft 7).

Primary Use Case

- Schema Safety: Prevents "Schema Drift" by locking down data structures before implementation.
- Decoupling: explicitly separates Inventory Data (Deck/Cost) from Entity Logic (Stats/Behavior), ensuring gameplay balancing does not break data persistence.
- API Contract: Defines the strict surface area for API endpoints (e.g., required vs. optional fields).

Methodology: Data Normalization

- Conflict Resolution: Resolved logical contradictions (e.g., defining Aggro Radius as an Abstract Enum rather than a Float).
- Abstraction: Converted qualitative gameplay mechanics into quantitative data types (e.g., "Siege Unit" $\\rightarrow$ TRAIT_SIEGE Enum).
- Constraint Application: Applied strict boundaries to open-ended mechanics (e.g., defining Cast Time as the rate-limiting mechanism).

Technical Constraints Implemented

1. Cardinality: Enforced strict 1:5 (Deck) and 1:1 (Titan) entity relationships.
2. State Machine: Modeled the Population Resource via a Semaphore pattern (Acquire on Spawn, Release on Death).
3. Data Typing:
   - Damage: Defined as True Damage (Integer), rejecting complex mitigation formulas.
   - Regen: Split into Rate (Float) and Delay (Float) to differentiate stateful vs. static behavior.
4. Abstraction Layer: Mechanics hidden in the engine (Siege Multipliers) are modeled as Tags to prevent null value pollution.

Design Intent: Volatility Resilience

- Static Architecture: Models the encyclopedic definition of game objects rather than live match states.
- Versioning: Enforces a game_version field on all entities to support immutable history across Early Access patches (e.g., Skeleton_v0.8 vs Skeleton_v0.9).

##

## **1\. Match Structure & Win Condition**

**Match Type:** 3v3 Multiplayer Arena (Hybrid RTS / MOBA / TPS).

**Duration:** Max 25 minutes.

### **Win Conditions**

1. **Destruction:** Destroy all 3 of the enemy team's **Lifestones**.
2. **Time Limit:** If 25:00 is reached, the team with the highest aggregate **Lifestone Health** wins. (Tie resolution: Unknown).

### **The Lifestones (Base Object)**

- **Function:** Primary objective and spawn point for Heroes.
- **Behavior:**
  - High Health.
  - Deals heavy single-target damage to enemies inside its radius.
  - **Death Rattle:** On destruction, releases a massive AOE explosion damaging all nearby units/heroes.

---

## **2\. The Player (Hero)**

**Identity:** One of 6 pre-made characters selected before the match.

**Progression:** Heroes level up during the match (Stat increases \+ Upgrade choices).

### **Hero Stats**

- **Vitals:** Health, Movement Speed, Flight Speed.
- **Regeneration:**
  - Health Regen Rate: Amount of HP recovered per second.
  - Regen Delay: Time (seconds) without taking damage before regen begins.
- **Combat:** Attack Damage (vs. Summoner), Attack Damage (vs. Minion).
- **States:** Grounded, Airborne (Flight/Jump), Dead/Respawning.

### **Hero Abilities (Fixed Kit)**

1. **Passive:** Always active trait.
2. **Primary Fire:** Melee or Ranged (TPS Aiming).
3. **Defense Skill:** Movement (Dash/Bunny Hop) or Mitigation (Shield).
4. **Ultimate:** High-impact unique ability.

### **Mechanics**

- **Movement:** WASD, Jumping, Flight (Hero dependent), "Bunny Hopping" (Velocity preservation).
- **Casting:**
  - **Standard:** Select Slot (1-4) $\\rightarrow$ Aim at valid surface $\\rightarrow$ Hold Left Click.
  - **Titan:** Select Slot (5/R) $\\rightarrow$ Aim at valid surface $\\rightarrow$ Hold 'R'.

---

## **3\. The Loadout (Deck)**

**Structure:** Fixed before the match. Cannot be edited during gameplay.

**Composition:** 5 Total Slots.

- **Slots 1-4:** Flex Slots (Creature, Building, or Spell).
- **Slot 5:** Titan Slot (Exclusive to Titan cards).

### **Card Rank Logic**

- **Distinct Items:** "Skeleton I" and "Skeleton IV" are separate database entities (not nested data).
- **Progression:** Players start with access to Rank I/II. Rank III/IV unlock via in-match leveling.
- **Restrictions:** Deck must contain at least one Rank I or Rank II CREATURE card.

---

## **4\. Economy & Resources**

Resources are managed **per-player**, not per-team.

### **Wallets (The "Cost" to play)**

1. **Charges (Ammo):**
   - Specific to each Card (e.g., Skeleton Card has 10 Charges).
   - Refills over **Time** or via **Pickups**.
   - _Constraint:_ Must have \>0 Charges to cast.
2. **Population (Cap):**
   - **Shared Supply:** Global limit shared by both **Units** and **Buildings**.
   - _Constraint:_ Current_Pop \+ Card_Cost \<= Max_Pop.
   - **Refund Mechanic:** Population cost is **immediately refunded** to the player upon the Unit/Building's death or destruction.
3. **Titan Charge (Global):**
   - 0-100% Fill Bar.
   - Fills via: Time, Combat actions.
   - _Cost:_ 100% to cast Titan.

### **XP (Progression)**

- **Source:** "Purple Crystals" dropped by minions/neutrals/objectives.
- **Effect:** Levels up Hero, unlocking Ranks and Upgrades.

---

## **5\. Entities (The "Things" in the Deck)**

### **A. Creatures (Minions)**

AI-controlled units that push lanes.

- **Stats:** Health, Attack Speed, Movement Speed, Range.
- **Combat Stats:**
  - Damage: Base damage dealt to enemies.
  - Heal Amount: (For Healers) Amount restored to allies.
- **Traits:**
  - **Siege:** Unit has a bonus multiplier vs. Structures (exact math hidden; treated as a Tag).
  - **Tank:** High threat/survivability unit (UI Label only).
  - **Debuffer:** Unit applies status effects (e.g., Anti-Heal).
  - **Healer:** Applies heal over time to nearby injured units.
- **Movement Types:**
  - _Ground:_ Obey terrain/walls.
  - _Hover:_ Ignores terrain roughness, respects height.
  - _Fly:_ Uses 3D airspace.
- **Behavior (AI):** Default push toward Lifestones.

### **B. Buildings (Structures)**

Static objects placed by players.

- **Stats:** Health. (No Duration/TTL—buildings persist until destroyed).
- **Placement Rules:**
  - Collision Radius: The circular footprint size used to check if the building fits in the world.
  - _Zone A:_ Anywhere (Friendly territory).
  - _Zone B:_ Specific (On Tower/Capture Points).
- **Types:** Walls (Blockers), Spawners, Utility (Buffs).

### **C. Spells (Actions)**

Instant effects.

- **Targeting:** Reticle (TPS), Lock-on, or PBAOE (Self).
- **Effects:** Damage, Heal, Buff/Debuff, Imbue Elemental Effect.

### **D. Titans (Super Units)**

- **Unique Constraint:** Only one active per player.
- **Stats:** Massive HP/Damage.
- **Variants:** Siege (Structure-Killer), Debuffer.

---

## **6\. Map & Environment**

### **Capture Points ("Towers")**

- **State:** Neutral $\\rightarrow$ Claimed (Red/Blue).
- **Mechanic:** Claiming spawns a defensive **Tower** (AI controlled).
- **Recapture:** Can be retaken by standing on point if the Tower is destroyed.

### **Loot (Chests)**

- **Content:** Temporary **Consumables**.
- **Inventory:** Separate 1-slot "Hand".
- **Items:** Small/Medium Heals, Charge Refills.
- **Lifecycle:** Items on the ground have a **Time-To-Live (TTL)** before despawning.

### **Neutrals (NPCs)**

- **Behavior:**
  - Default State: Hostile or Passive.
- **Reward:** XP (Purple Crystals) only.

## **7\. The Upgrade System (RNG)**

**Trigger:** Hero Level Up.

**Selection:** Player chooses 1 of 3 random options.

**Scope:**

1. **Global:** Increase Max Population, Increase Titan Damage.
2. **Specific:** Upgrade "Skeletons" (e.g., \+5 Charge Cap, \+10% HP).
   - _Note:_ Upgrades apply to specific Unit Tags or Ranks (e.g., "All Rank I units").

---

## **8\. Physics & Combat Rules (The Invisible Logic)**

### **Casting Physics**

- **Rate of Fire:** There is no Global Cooldown (GCD).
- **Cast Time:** Every card has a Cast Time (seconds). The player cannot act while casting. This acts as the effective fire-rate limit.

### **Projectiles vs. Hitscan**

- **Default:** Attacks are treated as **Projectiles** with travel time.
- **Stat:** Projectile Speed determines if an attack is dodgeable (Slow) or near-instant (Fast).

### **Damage Model**

- **Type:** **True Damage**.
- **Armor:** There is no Armor or Resistance stat. 10 Damage always reduces HP by 10\.

---

## **9\. Schema Architecture & Design Decisions**

_This section documents specific decisions made to translate the game mechanics into the JSON Schema structure._

### **A. The "Card vs. Entity" Split**

- **Decision:** We separated the **Card** (Cost, Deck Data) from the **Entity** (Stats, Health).
- **Reason:** This allows multiple Cards (Rank I, Rank II) to spawn the same Entity type with different stats, or for Game Logic (Upgrades) to modify the Entity without breaking the Card's cost logic.
- **Upgrade Targeting:** Entities must possess **Tags** (e.g., _undead, rank_1, melee_) to allow the Upgrade System to query and modify them correctly.

### **B. Omission of "Hidden Math"**

- **Decision:** We excluded fields for Structure Damage Multiplier and Aggro Radius.
- **Reason:** These values are likely hidden in the engine code. We replaced them with **Tags/Enums** (e.g., Trait: Siege, State: Hostile) which provide the necessary context for users without requiring impossible-to-get numbers.

### **C. The Healer Separation**

- **Decision:** We created distinct fields for Heal Amount and Damage.
- **Reason:** Prevents logic errors where a healer "attacks" a teammate. It allows a unit to theoretically do both (Hybrid) or only one (Pacifist Healer) without schema conflicts.

### **D. Static API with Versioning**

- **Decision:** All schemas include a game_version field.
- **Reason:** As an Early Access title, mechanics will change. This allows the API to serve as an encyclopedia for specific patches (e.g., "v0.8.2 Skeleton") rather than a live state tracker.

### **E. Handling Duration (TTL)**

- **Decision:** Removed duration from Buildings; kept duration (TTL) for Loot.
- **Reason:** Buildings are permanent until killed. Keeping a "Duration" field for them would result in null values for 90% of the database. Loot is the only temporary entity.
