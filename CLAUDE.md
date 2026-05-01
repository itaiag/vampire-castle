# Vampire Castle — Project Documentation

## Overview
Vampire Castle is a PyGame-based top-down exploration game where the player is a vampire reclaiming their castle. The game features:
- NPC recruitment through power usage
- Quest system with multiple objectives
- Ability/leveling progression
- Dialogue system with affinity mechanics
- Resource management (blood & suspicion)

**Launch**: `python main.py` (requires fullscreen)

## Architecture

### Entry Point & Scenes
- **main.py**: Entry point. Initializes pygame, login screen, then game loop
- **game.py**: Main game controller. Manages scenes, input handling, rendering

### Core Systems

#### Game Scenes (in game.py)
- `explore`: Top-down movement, NPC interaction, room exploration
- `interact`: Face-to-face with NPC, power selection menu
- `dialogue`: Conversation choices with affinity/preference bonuses
- `result`: Shows power outcome (success/fail) and consequences
- `levelup`: Choose ability to unlock after earning enough XP
- `court`: View recruited NPCs and their roles
- `journal`: Quest tracking with objectives and rewards
- `game_over`: Victory/defeat screen

#### Key Classes
- **Player** (player.py): Blood, suspicion, court, abilities, secrets
- **NPC** (npc.py): Affinity, state, role, dialogue tree, resistances
- **Castle** (castle.py): Room graph, NPC placement, exits
- **AbilitySystem** (abilities.py): Leveling, XP tracking, unlocks
- **QuestSystem** (quests.py): Quest triggers, objectives, rewards
- **SoundSystem** (sound.py): Ambient tracks, SFX playback
- **MapRenderer** (map_renderer.py): Top-down map visualization
- **PowerSystem** (powers.py): Read/Charm/Intimidate/Enthrall mechanics

### Data Structures

#### NPC State
```
NPCState: NEUTRAL, ENTHRALLED, CHARMED, FRIGHTENED, FLED
NPCRole: GUARD, SERVANT, PRIEST, NOBLE, HUNTER, ALCHEMIST
```

#### Power Results
```
PowerResult: SUCCESS, PARTIAL, FAIL, CRITICAL_FAIL
Result includes: power, result type, log message, dialogue,
                 blood cost, suspicion delta, affinity change
```

#### Quest Structure
```
Quest: title, description, objectives, status, quest_type (main/side)
Objective: description, completed flag
Rewards: blood, xp, suspicion_reduction, unlocks_room
```

## Key Systems

### NPC Interaction Flow
1. Player presses E to interact with NPC in room
2. Scene changes to "interact" showing NPC portrait & info
3. Player chooses power (1-4) or dialogue (T)
4. Power use triggers resistance check, affinity change
5. Result shown in "result" scene with consequences
6. On success, NPC joins court with assigned role

### Power System
- **Read Thoughts** (5 blood): Reveals NPC's secret, no affinity change
- **Charm** (10 blood): Increases affinity, variable success rate
- **Intimidate** (8 blood): Increases suspicion, creates FRIGHTENED state
- **Enthrall** (variable cost): Highest difficulty, creates ENTHRALLED state

Each power has success conditions based on:
- NPC's resistance to that power
- Current affinity level
- Player's passive abilities

### Dialogue System
- NPCs have dialogue trees (nodes by ID)
- Nodes have prerequisites (affinity requirement, must see other nodes)
- Player choices affect affinity, suspicion, blood
- NPC preferences (keywords) give bonus/penalty to affinity
- Marriage dialogue options trigger victory conditions

### Quest System
- Quests triggered by: power use on specific NPC, room visit, dialogue choice
- Objectives marked complete by triggers
- Main vs Side quest types
- Rewards: blood, XP, suspicion reduction, room unlocks
- Player claims rewards from journal (Q key)

### Leveling/Abilities
- XP awarded for successful power use
- At level thresholds, player gets ability choice (3 random offers)
- Abilities are PASSIVE (constant) or ACTIVE (cost blood to use)
- Can modify power mechanics (costs, resistances, effects)

## File Index

### Core Game
- `main.py` — Entry point, pygame init, login→game loop
- `game.py` — Game controller, scene management, rendering (1374 lines)
- `login.py` — Login/registration screen

### Game Systems
- `player.py` — Player character (blood, suspicion, court, secrets)
- `npc.py` — NPC class (affinity, state, dialogue, preferences)
- `castle.py` — Castle structure (rooms, connections, NPCs)
- `powers.py` — Power usage logic and resistance checks
- `abilities.py` — Ability system and leveling
- `quests.py` — Quest system and trigger checking
- `items.py` — Item system (currently minimal)

### Rendering & Audio
- `pixel_renderer.py` — Pixel art drawing (sprites, text, borders)
- `map_renderer.py` — Top-down castle map visualization
- `sound.py` — Sound system (ambient + SFX)

### Documentation Files
- `DIALOG_SYSTEM.md` — Detailed dialogue mechanics
- `PORTRAITS_AND_ROOMS.md` — Room descriptions & visual layout
- `DISTINCT_NPCS_AND_WALKING.md` — NPC differences & walking animation
- `NPC_VISUAL_DIFFERENCES.txt` — NPC visual distinctions

## Important Constants

### Layout (in game.py)
```python
W, H = 1024, 768        # Screen size
SIDEBAR_W = 260         # Right sidebar width
MAP_W = W - SIDEBAR_W   # Play area width
```

### Colors (in game.py)
```python
BG = (12, 8, 20)           # Dark purple background
BLOOD_RED = (180, 30, 40)  # For blood/danger
GOLD = (200, 170, 80)      # For important text/titles
WHITE = (230, 225, 240)    # Default text
MUTED = (140, 130, 160)    # Dimmed text
```

## Development Notes

### Debugging
- Event log on right sidebar shows game messages
- Map screen (M key) visualizes castle layout
- Console errors appear in terminal (check for pattern matches)

### Adding Content
1. **New NPC**: Define in castle.py, add dialogue tree (npc.py), portrait (pixel_renderer.py)
2. **New Quest**: Create in quests.py, set triggers and objectives
3. **New Ability**: Add to abilities.py with mechanics in powers.py or game.py
4. **New Room**: Add to castle.py with exits, description, elements

### Code Style
- Scene management in `_handle_key()` and `draw()`
- Drawing methods prefixed with `_draw_*`
- Event logging via `_log()` (wraps to 30 char width)
- Power dispatch in `_use_power()`

## Victory Conditions
1. **Marry Morgana**: Becomes ally, co-rule castle
2. **Marry Seraphine + Defeat Morgana**: Free castle from tyrant
3. **Game Over**: Hunters arrive (100 suspicion) or blood runs dry (≤0)

## Known Systems
- Walking animation between rooms (0.67s transition)
- NPC portrait keys map (NPC_PORTRAIT_KEYS dict)
- Conversation history (last 20 lines shown)
- Quest notification fade (3.5s display)
- Examined elements cycle (Q/Z keys)
