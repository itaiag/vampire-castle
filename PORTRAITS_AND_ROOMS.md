# NPC Portraits & Unique Rooms Guide

## Overview

Every NPC now has a **unique pixel art portrait** that appears during conversations, and each castle room has been completely redesigned with **distinctive descriptions, atmospheres, and visual layouts**.

---

## NPC Portraits

Each of the 7 NPCs has their own detailed 16x20 pixel portrait that displays during dialogue:

### 1. **Aldric the Guard** - The Grizzled Soldier
- **Appearance**: Scarred, weathered face with steel armor
- **Colors**: Grey armor, brown legs, weathered skin
- **Where**: Grand Entrance (start), talks about debts and loyalty
- **Display**: Shows during interact/dialogue scenes with full portrait

### 2. **Mira the Servant** - The Anxious Maiden
- **Appearance**: Young, soft face, nervous demeanor, servant's garb
- **Colors**: White dress, brown apron, delicate features
- **Where**: Old Kitchens
- **Display**: Smaller, gentler portrait with anxious expression

### 3. **Father Dorin** - The Stern Priest
- **Appearance**: Elderly, holding holy cross, religious robes
- **Colors**: Dark robes with golden cross
- **Where**: The Chapel
- **Display**: Solemn portrait with cross held at lips

### 4. **Lady Seraphine** - The Elegant Noble
- **Appearance**: Beautiful, composed, regal bearing
- **Colors**: Violet dress, purple cape, refined features
- **Where**: Upper Gallery
- **Display**: Sophisticated portrait with calm expression

### 5. **Viktor the Torturer** - The Scarred Brute
- **Appearance**: Massive, scarred, haunted eyes
- **Colors**: Grey armor, battle marks (X patterns), guilt in eyes
- **Where**: Dungeon Wing
- **Display**: Intimidating but tragic portrait

### 6. **Erasmus the Alchemist** - The Scholarly Mad Scientist
- **Appearance**: Wiry old man, intense gaze, scholarly
- **Colors**: Green robes, bright eyes, books in mind
- **Where**: Laboratory
- **Display**: Eccentric portrait with gleaming intelligence

### 7. **Isolde the Vampire Hunter** - The Seasoned Warrior
- **Appearance**: Lean, armed, dangerous, crossbow
- **Colors**: Blue armor, silver crossbow, determined eyes
- **Where**: East Tower
- **Display**: Combat-ready portrait with weapon visible

---

## Unique Room Descriptions

Each room is now **visually and thematically distinct** with 3-4 sentences of rich description and unique candle placements:

### Room 0: **The Grand Entrance**
- **Theme**: Reclamation & Memory
- **Description**: Twin staircases, your ancient sigil on marble floor, moonlight through stained glass
- **Atmosphere**: "Moonlight cuts through cracked stained glass. Somewhere, footsteps echo."
- **Candles**: 5 (dramatic corners + center)
- **NPC**: Aldric the Guard
- **Exits**: North to Kitchens, East to Chapel

### Room 1: **The Old Kitchens**
- **Theme**: Betrayal & Service
- **Description**: Cold hearth, iron pots, walls of portraits (your stewards now serving Voss), Mira dusting
- **Atmosphere**: "The hearth is dead. But the portraits remember."
- **Candles**: 3 (practical, mid-level)
- **NPC**: Mira the Servant
- **Exits**: South to Entrance, East to Gallery, North to Dungeon
- **Special**: Secret passage to room 4

### Room 2: **The Chapel**
- **Theme**: Holy vs. Unholy
- **Description**: Warped pews, crumbling altar, Dorin in prayer, holy objects gone
- **Atmosphere**: "The air tastes of incense and old faith. Something holy recoils from you."
- **Candles**: 5 (religious arrangement around altar)
- **NPC**: Father Dorin
- **Exits**: West to Entrance, North to Gallery

### Room 3: **The Upper Gallery**
- **Theme**: Past Haunting Present
- **Description**: Long windows overlooking courtyard, your defaced portrait with scratched-out eyes, Seraphine reading
- **Atmosphere**: "Your own face watches from the wall. She watches you watching it."
- **Candles**: 5 (distributed, softer lighting)
- **NPC**: Lady Seraphine
- **Exits**: West to Kitchens, South to Chapel, North to Throne Room, East to Laboratory

### Room 4: **The Throne Room**
- **Theme**: Power & Waiting
- **Description**: Your throne draped in Voss's colors, empty but waiting, sconces burning without hand
- **Atmosphere**: "The throne pulses with unfinished business. It remembers you."
- **Candles**: 5 (throne-focused, grand arrangement)
- **NPCs**: None (empty - where you rebuild court)
- **Exits**: South to Gallery
- **Special**: The heart of your castle, where you will sit again

### Room 5: **The Dungeon Wing**
- **Theme**: Pain & Guilt
- **Description**: Damp stone, metallic blood-smell, cells (some not empty), Viktor at his bench of tools
- **Atmosphere**: "Water drips in the dark. Each drop echoes like a scream."
- **Candles**: 3 (minimal, creates shadows)
- **NPC**: Viktor the Torturer
- **Exits**: South to Kitchens, East to Tower
- **Special**: Feed available (dangerous choice)

### Room 6: **The Alchemist's Laboratory**
- **Theme**: Forbidden Knowledge
- **Description**: Every surface active - bubbling apparatus, crystalline growths, unreadable formulae, mysterious glowing vial
- **Atmosphere**: "Chemical fire and strange energy. The air itself tastes wrong."
- **Candles**: 5 (distributed among dangerous equipment)
- **NPC**: Erasmus the Alchemist
- **Exits**: West to Gallery, North to Tower
- **Special**: Contains the anti-vampire poison vial

### Room 7: **The East Tower**
- **Theme**: Final Confrontation
- **Description**: Circular room at tower peak, arrow slits showing outside world, Isolde with crossbow raised
- **Atmosphere**: "The wind carries silver and determination. This is not chance. This is purpose."
- **Candles**: 3 (sparse, windy tower top)
- **NPC**: Isolde the Vampire Hunter
- **Exits**: South to Laboratory, West to Dungeon
- **Special**: Where the hunter has waited 20 years

---

## Visual Changes in Game

### During Interact Scene
- **Left side**: Large 4x scale NPC portrait with state-color aura
- **Right side**: Name, role, status, affinity meter, description excerpt
- **Below**: Dialogue box showing what they just said
- **Bottom**: Power selection menu

### During Dialogue Scene
- **Left side**: Extra-large 5x scale NPC portrait (more intimate)
- **Right side**: Full conversation history (10+ lines)
- **Top**: Affinity meter, relationship tracking
- **Available options**: Shown with prerequisites/requirements
- **Locked options**: Shown with reason why (grayed out)

### Room Exploration
- **Descriptions**: Much longer, richer narrative
- **Atmosphere**: Unique mood for each location
- **Candles**: Different placements create different lighting
- **NPCs**: Each in thematically appropriate setting

---

## Design Philosophy

**Portraits**: Each portrait communicates character at a glance:
- **Color palette**: Matches role and personality
- **Expression**: Shows current emotional state
- **Details**: Armor, tools, or items reveal profession
- **State aura**: Glows with relationship/status color

**Rooms**: Each location tells a story:
- **Past vs. Present**: Your ancient castle vs. Voss's occupation
- **Mood**: From sacred (chapel) to sinister (dungeon)
- **Physical Layout**: Candles create unique ambiance
- **Narrative**: Descriptions hint at hidden stories and secrets

---

## Code Implementation

### New Functions (pixel_renderer.py)
- `draw_npc_portrait()`: Renders detailed portraits at conversation size
- `NPC_PORTRAITS`: Dictionary of 16x20 pixel art grids (7 unique NPCs)
- New color codes: `X` (scars), `K` (leather), `+` (cross), `>/<` (weapons)

### Updated Methods (game.py)
- `_draw_interact()`: Now displays portrait on left side
- `_draw_dialogue()`: Now displays larger portrait with full conversation
- Both methods show affinity meter

### Enhanced Content (castle.py)
- All 8 room descriptions completely rewritten (2-4x longer)
- Unique atmosphere strings for each room
- Varied candle positions (3-5 per room) creating distinctive lighting
- Each room now feels like a real, lived-in location

---

## Tips for Players

1. **Study Portraits**: Each portrait shows character details in their appearance
2. **Read Room Descriptions**: Atmosphere hints at what challenges await
3. **Notice Lighting**: Candle placement affects mood and gameplay feel
4. **Track Affinity**: Portraits update with state colors as relationship changes
5. **Dialog is Visual**: Each NPC portrait is unique - they're not interchangeable

---

## Future Enhancements

Potential additions:
- Animated portraits (blinking, gestures)
- Different portraits for different emotional states
- Background paintings for each room
- More detail in room decorations
- Seasonal/time-of-day variations in lighting
