# Changelog

All notable changes to pygkit are documented here.

## Unreleased

### Features

- `pack_spritesheet` gained a `columns` option (via the `PackOptions`
  TypedDict, now used with `Unpack` for typed kwargs): for
  `target="file"` it wraps the flat frame list into rows of at most
  `columns` frames — `columns=1` stacks frames vertically (one per
  row), `columns=4` wraps every 4. A short last row is padded with
  transparent cells so the sheet stays a clean grid readable by
  `AnimationSheet` with `cols=columns`. The `"animation"` label (when
  `add_label=True`) attaches after the last row's frames.

### Typing

- `pack_spritesheet(**kwargs)` is now annotated
  `**kwargs: Unpack[PackOptions]`, so type checkers catch unknown or
  mistyped pack options instead of passing them through untyped.

## 2.2.0 (2026-11-12)

### Breaking changes

- Removed `ButtonStyle` from `pygkit.ui` and `pygkit` exports. Style
  buttons with `UIStyle` dicts passed through the widget's `style=`
  argument (per-state paint: `bg`/`fg`/`gradient`/`border`/`radius`/
  `shadow`).
- `UIOptions` is geometry-only: the appearance keys `background` and
  `border_radius` no longer exist. Move them into a `UIStyle`
  (`bg`, `radius`, ...) and pass it via `style=`. Width/height and
  other geometry keys are unchanged.
- `Menubar` takes `background_image=` (with `image=` as an alias)
  instead of an `image=`-only parameter; passing both raises.

### Features

- Added `pygkit.ui.theming`: a data-driven style system. One `UIStyle`
  dict describes a widget's paint (background/foreground color,
  vertical `gradient`, `border`, `shadow`, corner `radius`) per
  interaction state (`normal` / `hover` / `pressed` / `disabled` /
  `selected`). Styles validate strictly (`validate_style` raises on
  unknown keys or bad values) and resolve through a widget ancestry
  chain with partial overrides (`resolve_style`).
- Added `Panel` widget: a styled, optionally gradient/bordered box for
  grouping content, driven by the same `UIStyle` system.
- `Button` supports image-backed states: `background_images` maps the
  five state keys to surfaces, drawn instead of engine chrome (gradient,
  border, background), so skinned art is the chrome.
- Layout: `HBox` / `VBox` gained cross-axis alignment, and flow boxes
  hug their ink (no leading space from the origin seed).
- `Menubar` routes events through layout children, so nested
  `HBox` / `VBox` / `GridBox` leaves receive events via their own
  `handle_event`, re-layouts automatically on size changes, and no
  longer registers phantom hit rects before the first render.

### Cleanup

- Source is comment-free: explanatory chatter, TODOs, and section
  divider comments stripped; docstrings kept as the sole in-code docs.
- Removed scratch files (`usecase.temp.md`, `temp/` probes) from the
  tree.
- Expanded test suite for the style system, panel, layout, menubar
  event routing, and background-image buttons.

## 2.1.1 (2026-10-23)

- Added `pygkit.ui` layout system: `AnchorLayout`, `HBox`, `VBox`,
  and `GridBox` containers for flow and grid arrangements.
- `CooldownOverlay` sweep collapses to a flat rect border when the
  style radius is 0.

## 2.1.0 (2026-10-09)

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
- `AnimationSheet` supports cell offsets via `start_row`/`start_col` with
  full-grid sizing from `sheet_rows`/`sheet_cols`, so a `rows` x `cols`
  window can start at any cell instead of the first row/column.
- Added `pygkit.lighting`: generic 2D lighting pipeline with a low-resolution
  light map (`LightMap`), radial lights with organic flicker (`PointLight`),
  wind-reactive flame lights (`DynamicLight`), and mouse-aimable cone lights
  (`Spotlight`).
- Full `BLEND_RGB_*` and `BLEND_RGBA_*` (MULT/ADD/SUB/MIN/MAX) support for
  light compositing, including negative lights for shadows.
- Added `examples/lighting_demo.py` (night scene with torch, wind-controlled
  campfire, shadows, spotlight, blend/scale/pixelated toggles, FPS counter).

## 2.0.0 (2026-10-09)

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
- New `pygkit.parallax` subsystem: `ParallaxBackground` / `ParallaxLayer`
  with per-axis factors and `tile` / `clamp` / `once` modes, plus a small
  `Camera2D` (follow, deadzone, bounds, drift, shake).

## 0.1.0

- Initial release
- UIBase with box model and plugin compositing
- ProgressBarUI, CooldownOverlay, Container widgets
- SoundManager with main/sfx channel pools
- Timer utility
- Interpolation utilities (lerp, smoothstep, SimpleInterpolation)
