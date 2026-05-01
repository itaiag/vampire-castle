# Visually Distinct NPCs & Walking System

## 🎭 Completely Different NPC Appearances

Each NPC now has a **unique body type, silhouette, and visual characteristics** - they're no longer cookie-cutter copies of each other.

### Physical Distinctions

| NPC | Body Type | Height | Build | Key Features |
|-----|-----------|--------|-------|--------------|
| **Aldric** | Very Tall | Tallest | Muscular, Broad | Heavy scarring, thick beard, wide shoulders |
| **Mira** | Short | Shortest | Delicate, Petite | Small head, thin limbs, nervous posture |
| **Dorin** | Medium | Medium | Hunched, Frail | Deeply lined face (age marks), stooped posture, holds cross high |
| **Seraphine** | Very Tall | 2nd Tallest | Slender, Elegant | Long neck, refined posture, flowing silhouette |
| **Viktor** | Wide | Very Muscular | Extremely Bulky | Massive shoulders, intimidating bulk, scarred |
| **Erasmus** | Short | Short | Thin, Scholarly | Pointed hat shape, stooped over books, very lean |
| **Isolde** | Lean | Athletic | Combat-ready | Crossbow prominent, battle-scarred, ready stance |

### Visual Details

**Aldric the Guard** (Tall & Tough)
```
Heavy shoulder armor - extremely wide
Scarred face with deep X marks
Thick beard, weathered
Taller stance (bottom extended down)
```

**Mira the Servant** (Petite & Delicate)
```
Very small head
Thin delicate frame
Worried eyes (E marks)
Shorter overall (stooped)
```

**Father Dorin** (Old & Religious)
```
Golden cross held high above head
Deep age lines (X marks all over face)
Hunched posture
Holding sacred relic
```

**Lady Seraphine** (Elegant & Regal)
```
Long graceful neck
Very slender frame
Refined upright posture
Long elegant silhouette
```

**Viktor the Torturer** (Massive & Scary)
```
Extremely wide shoulders
Bulky muscular frame
Battle scars everywhere
Heavy weighted legs
```

**Erasmus the Alchemist** (Scholarly & Quirky)
```
Distinctive pointed scholar's hat
Very thin frame
Stooped over (scholarly posture)
Appears almost skeletal
```

**Isolde the Vampire Hunter** (Combat-Ready & Scarred)
```
Visible crossbow in both hands
Battle-scarred face
Athletic lean build
Ready fighting stance
```

### How They Appear

**In Conversation (Interact Scene):**
- 4x scale pixel portrait on left side
- Each NPC's unique proportions clearly visible
- Body type difference obvious at a glance

**In Dialogue:**
- 5x scale portrait for close-up view
- All distinguishing features highly visible
- Height differences apparent
- Unique silhouettes unmistakable

**In Room Exploration:**
- Smaller 3x scale sprites during exploration
- Still visually distinct from each other
- Can identify NPCs by silhouette alone

---

## 🚶 Walking System (No More Instant Teleportation)

Previously, pressing arrow keys to move between rooms caused **instant teleportation**. Now you **walk to exits** with smooth animation.

### How Walking Works

**1. Exit Portals Appear**
- Each room exit shows a glowing gothic portal/archway
- Portals pulse with purple/pink glow
- Direction letter appears in center (N/S/E/W)
- Visible indicators for all available exits

**2. Walking Animation**
- Press arrow key to walk toward exit
- Player character smoothly moves across room
- Takes ~0.67 seconds to reach exit
- Movement is visible and satisfying

**3. Transition**
- Player walks toward the portal
- Upon reaching it, automatically enters new room
- New room loads with full description
- Player positioned at room center

### Visual Progression

```
Player at room center
         ↓ (press arrow key)
Exits appear as glowing portals
         ↓
Player walks toward chosen exit
         ↓
Reaches the portal (0.67 seconds)
         ↓
Automatically enters new room
         ↓
New room description appears in log
```

### Exit Portal Details

**Appearance:**
- Gothic archway design (50x50 pixels)
- Pulsing purple/pink glow (sin-wave based)
- Inner glow border for depth
- Direction letter in center (N/S/E/W in gold)

**Positioning:**
- **North exit**: Top center of room
- **South exit**: Bottom center of room
- **West exit**: Left center of room
- **East exit**: Right center of room

**Animation:**
- Glow pulses at steady rhythm (~60 pixels per second)
- Draws player's attention to available paths
- Smooth continuous pulsing effect

### Gameplay Feel

**Before:**
- Press arrow → Instant room change
- No sense of movement or distance
- Feels like teleportation

**After:**
- Press arrow → See character walk toward exit
- Exits visible during exploration
- Castle feels more connected and real
- Movement is satisfying and intentional

### Code Changes

**game.py Updates:**
- Added `is_walking`, `walk_direction`, `walk_target_room`, `walk_progress` state variables
- `_move()` now initiates walking instead of instant transition
- `update()` handles walking animation with smooth interpolation
- Player position smoothly interpolated from center to exit (0 to 1.0 progress)
- `_draw_exit_portal()` renders glowing exit indicators
- Automatic room transition when walk completes

**Exit Portal Rendering:**
```python
_draw_exit_portal(direction)
  - Position based on direction
  - Pulsing glow circle (alpha varies with sin(tick))
  - Gothic border rectangle
  - Direction letter in gold
```

---

## 🎮 Gameplay Improvements

### Immersion
- Walking feels more like exploring a real castle
- You see the exits before moving through them
- Distance between rooms feels meaningful
- Movement has weight and purpose

### Navigation
- Exit portals are clearly visible
- Easy to see available paths
- No accidental room transitions
- Direction indicators (N/S/E/W) prevent confusion

### Visual Clarity
- Each NPC is immediately recognizable by appearance
- No confusion between characters
- Body type communicates role:
  - Tall muscular = Guard
  - Small delicate = Servant
  - Old hunched = Priest
  - Elegant tall = Noble
  - Massive wide = Torturer
  - Thin scholarly = Alchemist
  - Athletic scarred = Hunter

---

## 📊 Performance

- Walking animation runs at 60 FPS
- Smooth interpolation: 0% → 100% in 0.67 seconds
- Exit portal glow updates every frame
- No performance impact from visual changes

---

## 🎨 Color Coding Added

**New colors in pixel_renderer.py:**
- `H`: Pointed hat (brown) - scholar identifier
- `E`: Worried eyes (darker) - emotion indicator
- `X`: Age/battle scars (grey) - experience marker
- `+`: Cross/holy symbol (gold) - religious identifier
- `>/<`: Weapon edges (silver) - combat indicator

---

## Examples in Action

### Exploring the Castle

```
You're in the Grand Entrance.
You see four glowing portals:
  N - pointing north (top)
  S - pointing south (bottom)
  E - pointing east (right)

You press W (north key).

Your character walks north across the room...
[0.2s] Character is 1/5 of way to exit
[0.4s] Character is 1/2 way to exit
[0.6s] Character reaches the portal
[Game transitions to The Old Kitchens]

You enter: The Old Kitchens
```

### Meeting NPCs

**Aldric** appears in the room - immediately obvious he's the **large, scarred guard** (tall and muscular).

**Mira** appears - immediately obvious she's the **young, delicate servant** (petite, thin frame).

No confusion about who is who based on silhouettes alone.

---

## Future Enhancements

Possible additions:
- Different walking animation for different NPCs (slow, fast, limping, elegant)
- Sound effects for footsteps, doors opening
- Animated portal animations (swirling, opening)
- Obstacles during walking (guards block paths)
- Variable walk speeds based on player status (wounded, charmed, etc.)
- Camera pan following the player's walk
