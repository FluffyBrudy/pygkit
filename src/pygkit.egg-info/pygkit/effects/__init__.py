"""
Effect system for pygkit - modular, composable visual effects.

This module provides building blocks for creating visual effects that can be
used for scene transitions, UI animations, lighting, and dynamic game effects.

Core Concepts:
- EffectSurface: Surface wrapper with automatic caching and blend mode chaining
- Generators: Pure functions producing textures (gradients, noise, patterns)
- Compositors: Blend mode wrappers with semantic names
- Components: Stateful effect units with parameters and update/render methods
- Transitions: Adapters to use effects as scene transitions
"""

from pygkit.effects.base import EffectComponent, EffectSurface, cached_generator
from pygkit.effects.generators import (
    radial_gradient,
    linear_gradient,
    noise_texture,
    checker_pattern,
    distance_field_circle,
    distance_field_rect,
    composite,
)
from pygkit.effects.compositors import (
    BlendMode,
    Compositor,
    blend_add,
    blend_multiply,
    blend_screen,
    blend_overlay,
    alpha_blend,
    lerp_blend,
)
from pygkit.effects.components import (
    # Lighting
    LightSource,
    AmbientLight,
    GlowPulse,
    Flash,
    # Masks
    NoiseMask,
    ShatterMask,
    ThresholdReveal,
    DisplacementMap,
    # Color
    ColorTint,
    Grayscale,
    ChromaticAberration,
    Vignette,
    ColorShift,
)
from pygkit.effects.transitions import (
    EffectTransition,
    ShatterBlastTransition,
    NoiseDissolveTransition,
    LightSweepTransition,
)

__all__ = [
    # Core classes
    "EffectSurface",
    "EffectComponent",
    "cached_generator",
    "Compositor",
    "composite",
    "blend_add",
    "blend_multiply",
    "blend_screen",
    "blend_overlay",
    "alpha_blend",
    "lerp_blend",
    # Generators
    "radial_gradient",
    "linear_gradient",
    "noise_texture",
    "checker_pattern",
    "distance_field_circle",
    "distance_field_rect",
    # Compositors
    "BlendMode",
    # Components - Lighting
    "LightSource",
    "AmbientLight",
    "GlowPulse",
    "Flash",
    # Components - Masks
    "NoiseMask",
    "ShatterMask",
    "ThresholdReveal",
    "DisplacementMap",
    # Components - Color
    "ColorTint",
    "Grayscale",
    "ChromaticAberration",
    "Vignette",
    "ColorShift",
    # Transitions
    "EffectTransition",
    "ShatterBlastTransition",
    "NoiseDissolveTransition",
    "LightSweepTransition",
]
