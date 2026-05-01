# Dialog Relationship System

## Overview

The dialog system now features:
- **Relationship Tracking**: Each NPC has an affinity score (0-100)
- **Progressive Unlocking**: Dialog options unlock based on previous choices and relationship level
- **Rewards System**: Conversations can grant blood, modify suspicion, and increase affinity
- **Vampire Secret**: NPCs can discover the player is a vampire through specific dialog paths
- **Rich Conversation History**: Up to 10 lines of dialog shown at once (was 6)

## How It Works

### 1. Dialogue Nodes
Each dialog option is now a `DialogNode` with:
```python
DialogNode(
    id="unique_id",                    # unique identifier
    text="What player says",           # dialog choice text
    response="What NPC says",          # NPC's response
    requires=["prev_node_id"],         # prerequisites (must see first)
    min_affinity=15,                   # relationship threshold
    affinity_change=+5,                # how much relationship changes
    blood_reward=20,                   # blood gained/spent (positive/negative)
    suspicion_change=-5,               # castle suspicion impact
    option_type=DialogueOption.HELP_SEEKING,  # categorization
    shows_vampire_hint=False,          # reveals vampire nature if True
)
```

### 2. Affinity System
- **Starting affinity**: 0/100 for each NPC
- **Building rapport**: Each conversation choice changes affinity
- **Unlocking advanced dialogue**: Some options only appear once affinity reaches a threshold
- **Visible in UI**: Affinity meter shown during dialog with each NPC

### 3. Dialog Progression Example (Aldric the Guard)

**Initial Options** (all available at 0 affinity):
- "Why do you serve Count Voss?" (+2 affinity)
- "You look troubled. What weighs on you?" (+5 affinity)
- "Do you remember the castle's old lord?" (+3 affinity)

**Mid-Level Options** (after affinity ≥15):
- "I could help you with those debts." (requires "troubled" option seen, +10 affinity, -20 blood cost, -5 suspicion)

**Advanced Options** (after affinity ≥30):
- "I'm not what you think I am. But I can protect your family better than any moneylender." (REVEALS VAMPIRE NATURE, +15 affinity)

### 4. Vampire Secret Mechanic
- **Goal**: Keep your vampire nature secret from most NPCs
- **Father Dorin**: Already knows (starts with `suspects_vampire=True`)
- **Other NPCs**: Can discover through specific dialog paths marked with `shows_vampire_hint=True`
- **UI Indicator**: "⚠ Knows your secret" appears in dialog UI if NPC is suspicious
- **Consequences**: NPCs who discover treat you differently (higher resistance to powers)

### 5. Dialog Rewards
Conversations can provide:
- **Blood**: Positive values heal, negative costs blood (e.g., helping someone costs you)
- **Suspicion**: Change castle-wide alert level (negative is better)
- **Affinity**: Automatically tracked

Example: Helping Aldric with debt (aldric_4)
- Costs 20 blood
- Reduces suspicion by 5
- Gains 10 affinity

### 6. Locked Dialog Display
- **Available options**: Shown with `[1] [2] [3]` in gold text
- **Locked options**: Shown with lock icon and reason:
  - "Need closer relationship (15/25)" → need more affinity
  - "Requires earlier conversation" → need to see prerequisite first

### 7. Extended Conversation History
- **Display**: Up to 10 lines of conversation visible (instead of 6)
- **Multi-line wrapping**: Long messages automatically wrap
- **Speaker tags**: "You:" vs "NPC name:" in different colors
- **Persistent**: Conversation carries across multiple dialog visits

## NPCs with Dialogue Trees

### Aldric the Guard
**Role**: Guard
**Theme**: Debt-ridden soldier torn between duty and survival
**Loyalty path**: Help with debts → Offer protection as alternative to moneylender → Reveals vampire nature
**Rewards**: -5 suspicion, +20 affinity, -20 blood

### Mira the Servant
**Role**: Servant
**Theme**: Granddaughter of your old steward, knows castle secrets
**Loyalty path**: Show you knew her grandfather → Reveal you've lived centuries → Get access to hidden passages
**Rewards**: -10 suspicion, +20 affinity

### Father Dorin
**Role**: Priest
**Theme**: Hunter who's been waiting for your return
**Note**: Already suspects you're a vampire!
**Approaches**: Show respect, learn from him, maybe convince him you're not a threat
**Challenge**: Very high resistance to powers, won't be charmed easily

### Lady Seraphine
**Role**: Noble
**Theme**: Wants to poison her father, intrigued by the supernatural
**Loyalty path**: Learn her secret → Reveal you know about poison → Offer to help eliminate Voss → Reveal vampire nature
**Rewards**: -15 suspicion, +10 blood, +20 affinity

## Adding More Dialogue

To add dialog options for an NPC:

```python
npc.add_dialogue(DialogNode(
    id="unique_id",
    text="What you say",
    response="What NPC says",
    requires=["previous_node_id"],  # if this should unlock after another
    min_affinity=10,                # if this needs relationship threshold
    affinity_change=+5,             # how it affects relationship
    blood_reward=0,                 # positive=gain, negative=cost
    suspicion_change=0,             # positive=worse, negative=better
    option_type=DialogueOption.NEUTRAL,  # NEUTRAL, FLIRTY, THREATENING, HELP_SEEKING, REVEALING_HINT
    shows_vampire_hint=False,       # does this reveal you're a vampire?
))
```

## Gameplay Tips

1. **Talk before using powers**: Dialogue builds rapport without suspicion
2. **Plan your approach**: Some NPCs are easier to win over through conversation
3. **Unlock advanced options**: High affinity reveals more powerful dialog choices
4. **Hide your nature**: Avoid `shows_vampire_hint` options with NPCs you want to keep fooled
5. **Use rewards**: Dialog can provide blood and reduce suspicion more safely than powers

## Code Changes

- **npc.py**: Added `DialogNode` class, `DialogueOption` enum, affinity/relationship tracking, dialogue tree system
- **game.py**:
  - `_dialogue_key()`: Now processes DialogNode rewards (blood, suspicion, affinity)
  - `_draw_dialogue()`: Enhanced to show affinity meter, more conversation history, locked dialog with reasons
  - Conversation history increased from 12 to 20 lines max
