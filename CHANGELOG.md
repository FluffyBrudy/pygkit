# Changelog

## Unreleased

### Features

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
