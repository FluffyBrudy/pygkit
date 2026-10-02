# pygkit

General-purpose Pygame CE runtime kit: UI widgets, audio management, timers, interpolation, and utilities.

## Quick Start

```python
import pygkit
```

## Features

- **UI**: Box-model widgets with plugin compositing — progress bars, cooldown overlays, containers, dialog system, buttons, menubar container, anchor/row/grid placement helpers
- **Animation**: Multi-state `AnimationPlayer` where every state owns its own spritesheet — mixed image sizes and grids (e.g. `idle_spritesheet.png` vs `run_spritesheet.png`) in one player; pure image API, no JSON
- **Dialog**: Typewriter effect with customizable speeds, speaker names, and progress indicators
- **Inventory**: Grid-based item management with stacking, weight tracking, events, and serialization
- **Audio**: SoundManager with channel pools, kind/key addressing, volume buses, fades
- **Lighting**: low-resolution light map pipeline (`LightMap`), point lights
  with flicker, wind-reactive `DynamicLight` flames, and cone `Spotlight` —
  full RGB/RGBA blend modes, allocation-free per frame
- **Transitions**: Screen transitions with fade, wipe, and custom effects
- **Utils**: Timer, interpolation/easing functions

## Installation

```bash
pip install pygkit            # core: signals, utils, protocols
pip install "pygkit[ui]"      # widgets, dialog, cooldowns
pip install "pygkit[all]"     # everything
```

Available extras: `ui`, `audio`, `animation`, `lighting`,
`transitions`, `inventory`, `parallax`, `all`. `import pygkit` alone loads
core only; subsystems load lazily on first use.

> Extra: lightning idea was extended version of [https://www.youtube.com/watch?v=LN7u20H7zK4](https://www.youtube.com/watch?v=LN7u20H7zK4) which was my first attempt of making lightning after learning blend modes.
