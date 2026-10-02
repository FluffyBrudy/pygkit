# Changelog

## 2.0.0

One rule for time now: everything takes `dt` in seconds. Give each
thing its `dt` every frame and the whole game pauses and slows down
together:

```python
cooldown = Timer(3.0)

while running:
    dt = clock.tick(60) / 1000
    cooldown.update(dt)
    dialog.update(dt)
    player.update(dt)
    if cooldown.reached():
        ...
```

What changed:

- `Timer` takes seconds (like `3.0` for 3 seconds) and only moves when
  you call `update(dt)`. You can pause, resume, slow down, and repeat
  any timer. If you used the old `Timer`, swap millisecond numbers for
  seconds (`3000` becomes `3.0`) and add one `update(dt)` per frame.
- Animations use seconds too (`player.update(dt)` instead of
  milliseconds), so there is only one unit to remember.
- Dialog boxes, cooldown icons, and containers all update with `update(dt)`.
- Fades, wipes, and shakes can be paused, reject bad durations instead
  of crashing, and start in a clean idle state.
- Progress bars smooth out based on real time, so they look the same
  at 30 fps and 144 fps.
- Sounds: fade-ins actually fade now, and stopping or muting one sound
  affects every copy of it playing.
- Lights: changing a light's size or color takes effect right away,
  and bad sizes are rejected instead of drawing garbage.
- Inventory drag-and-drop no longer loses or duplicates items, and
  inventory panels can be shown and hidden.
- Buttons and menus accept all layout options, and clicking them hits
  where you expect.

## Unreleased

### Features

- Slim core install: `import pygkit` loads signals, utils, protocols
  only; subsystems (ui, audio, animation, lighting, transitions,
  inventory) load lazily. Install what the game uses:
  `pip install "pygkit[ui]"`, `...[all]` for everything.
- `pygkit.inventory` names now resolve from the top level
  (`from pygkit import Inventory`).
- `SoundManager.play` returns the live `Channel`; new `volume` /
  `fade_ms` playback kwargs. Kind/key addressing via `channel_for`
  / `playing`, scoped `stop` / `fadeout`, and master x kind x sound
  volume buses with live-apply (`set_volume` / `get_volume`).
- Added `pygkit.ui.Button`: text or image-backed button with typed
  `ButtonStyle` tint overlays, `on_press` signal, passive
  press/activate hit-testing. Added `pygkit.ui.Menubar`: container
  with local child rects, 9-anchor placement, `add`/`remove`, and
  `handle_event` returning whether a child claimed the event.
- Added `pygkit.ui.anchors`: `place`/`row`/`column`/`grid` helpers
  on `pygame.Rect` anchor names. Added `Clickable` protocol.
  See `examples/menubar_demo.py`.
- Removed self-claiming "production-grade" wording from docs.

- `AnimationSheet` supports cell offsets via `start_row`/`start_col` with
  full-grid sizing from `sheet_rows`/`sheet_cols`, so a `rows` x `cols`
  window can start at any cell instead of the first row/column.
- Added `pygkit.lighting`: generic 2D lighting pipeline with a low-resolution
  light map (`LightMap`), radial lights with organic flicker (`PointLight`),
  wind-reactive flame lights (`DynamicLight`), and mouse-aimable cone lights
  (`Spotlight`).
- `DynamicLight` regenerates its glow at light map resolution when the
  user-fed wind vector crosses a direction/strength bucket (~1 ms per
  regeneration, ~0 ms per frame in steady state), with optional periodic
  re-bakes for a dancing flame.
- Full `BLEND_RGB_*` and `BLEND_RGBA_*` (MULT/ADD/SUB/MIN/MAX) support for
  light compositing, including negative lights for shadows.
- Light map pipeline is allocation-free per frame (reused surfaces, cached
  sprites, angle-bucketed rotation cache); ~1000 fps headless at 960x600
  with a static and a dynamic light.
- Added `examples/lighting_demo.py` (night scene with torch, wind-controlled
  campfire, shadows, spotlight, blend/scale/pixelated toggles, FPS counter).

## 0.1.0 (unreleased)

- Initial release
- UIBase with box model and plugin compositing
- ProgressBarUI, CooldownOverlay, Container widgets
- SoundManager with main/sfx channel pools
- Timer utility
- Interpolation utilities (lerp, smoothstep, SimpleInterpolation)
