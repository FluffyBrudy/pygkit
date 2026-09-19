"""pygkit - Pygame CE runtime kit.

Core (signals, utils, protocols) imports eagerly. Subsystems load
lazily on first attribute use, so ``import pygkit`` stays cheap::

    pip install pygkit          # core only
    pip install "pygkit[ui]"    # + widgets, dialog, cooldowns
    pip install "pygkit[all]"   # everything
"""

from __future__ import annotations

import importlib
from typing import Any

from .protocols import Drawable, Renderable, UIElement, Updateable
from .signals import Signal, SignalBus, signal
from .utils import (
    SimpleInterpolation,
    Timer,
    ease_in,
    ease_in_out,
    ease_out,
    fit,
    lerp,
    load_font,
    outline,
    render_multiline,
    shadow,
    smoothstep,
    wrap,
)

_LAZY_ATTRS: dict[str, str] = {
    "SoundManager": "audio",
    "SFX_CHANNELS": "audio",
    "AnimationPlayer": "animation",
    "AnimationSheet": "animation",
    "PackOptions": "animation",
    "pack_spritesheet": "animation",
    "LightMap": "lighting",
    "PointLight": "lighting",
    "Spotlight": "lighting",
    "DynamicLight": "lighting",
    "glow_sprite": "lighting",
    "spotlight_sprite": "lighting",
    "dynamic_glow_sprite": "lighting",
    "clear_sprite_cache": "lighting",
    "RGB_ADD": "lighting",
    "RGB_SUB": "lighting",
    "RGB_MULT": "lighting",
    "RGB_MIN": "lighting",
    "RGB_MAX": "lighting",
    "RGBA_ADD": "lighting",
    "RGBA_SUB": "lighting",
    "RGBA_MULT": "lighting",
    "RGBA_MIN": "lighting",
    "RGBA_MAX": "lighting",
    "LIGHT_ADD": "lighting",
    "SCENE_MULT": "lighting",
    "TransitionRunner": "transitions",
    "TransitionState": "transitions",
    "FadeToBlack": "transitions",
    "FadeFromBlack": "transitions",
    "Crossfade": "transitions",
    "Flash": "transitions",
    "IrisIn": "transitions",
    "IrisOut": "transitions",
    "Slide": "transitions",
    "PixelDissolve": "transitions",
    "Shake": "transitions",
    "Container": "ui",
    "CooldownOverlay": "ui",
    "ProgressBarUI": "ui",
    "UIBase": "ui",
    "UIOptions": "ui",
    "BoxModel": "ui",
    "BoxModelResult": "ui",
    "generate_box_model": "ui",
    "DialogBox": "ui",
    "DialogConfig": "ui",
    "DialogColors": "ui",
    "DialogLine": "ui",
    "TypewriterSpeed": "ui",
    "ItemData": "inventory",
    "InventoryConfig": "inventory",
    "ItemStack": "inventory",
    "InventoryEvent": "inventory",
    "RARITY_COLORS": "inventory",
    "DEFAULT_INVENTORY_CONFIG": "inventory",
    "Inventory": "inventory",
    "AssetCache": "inventory",
    "get_cache": "inventory",
    "generate_procedural_icon": "inventory",
    "render_quantity_text": "inventory",
    "Tooltip": "inventory",
    "DragDropState": "inventory",
    "InventoryWidget": "inventory",
    "InventoryManager": "inventory",
}

__all__ = [
    "SoundManager",
    "SFX_CHANNELS",
    "AnimationPlayer",
    "AnimationSheet",
    "PackOptions",
    "pack_spritesheet",
    "LightMap",
    "PointLight",
    "Spotlight",
    "DynamicLight",
    "glow_sprite",
    "spotlight_sprite",
    "dynamic_glow_sprite",
    "clear_sprite_cache",
    "RGB_ADD",
    "RGB_SUB",
    "RGB_MULT",
    "RGB_MIN",
    "RGB_MAX",
    "RGBA_ADD",
    "RGBA_SUB",
    "RGBA_MULT",
    "RGBA_MIN",
    "RGBA_MAX",
    "LIGHT_ADD",
    "SCENE_MULT",
    "TransitionRunner",
    "TransitionState",
    "FadeToBlack",
    "FadeFromBlack",
    "Crossfade",
    "Flash",
    "IrisIn",
    "IrisOut",
    "Slide",
    "PixelDissolve",
    "Shake",
    "Container",
    "CooldownOverlay",
    "ProgressBarUI",
    "UIBase",
    "UIOptions",
    "BoxModel",
    "BoxModelResult",
    "generate_box_model",
    "DialogBox",
    "DialogConfig",
    "DialogColors",
    "DialogLine",
    "TypewriterSpeed",
    "ItemData",
    "InventoryConfig",
    "ItemStack",
    "InventoryEvent",
    "RARITY_COLORS",
    "DEFAULT_INVENTORY_CONFIG",
    "Inventory",
    "AssetCache",
    "get_cache",
    "generate_procedural_icon",
    "render_quantity_text",
    "Tooltip",
    "DragDropState",
    "InventoryWidget",
    "InventoryManager",
    "SimpleInterpolation",
    "Timer",
    "lerp",
    "smoothstep",
    "ease_in_out",
    "ease_out",
    "ease_in",
    "load_font",
    "outline",
    "shadow",
    "wrap",
    "render_multiline",
    "fit",
    "Signal",
    "SignalBus",
    "signal",
    "Renderable",
    "UIElement",
    "Drawable",
    "Updateable",
]


def __getattr__(name: str) -> Any:
    try:
        sub = _LAZY_ATTRS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    module = importlib.import_module(f"{__name__}.{sub}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(__all__)
