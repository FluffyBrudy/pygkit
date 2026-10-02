import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

import pygkit
from pygkit import _LAZY_ATTRS

SUBSYSTEMS = ("audio", "animation", "lighting", "transitions", "ui", "inventory", "parallax")

CORE_NAMES = (
    "Drawable",
    "Renderable",
    "UIElement",
    "Drawable",
    "Updateable",
    "Clickable",
    "Widget",
    "Signal",
    "SignalBus",
    "signal",
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
)


def test_lazy_map_matches_submodule_all():
    expected: dict[str, str] = {}
    for sub in SUBSYSTEMS:
        mod = importlib.import_module(f"pygkit.{sub}")
        for name in mod.__all__:
            assert name not in expected, f"{name!r} exported by two subsystems"
            expected[name] = sub
    assert _LAZY_ATTRS == expected


def test_all_covers_core_and_lazy():
    assert set(pygkit.__all__) == set(CORE_NAMES) | set(_LAZY_ATTRS)
    assert len(pygkit.__all__) == len(set(pygkit.__all__))


def test_core_names_eager():
    for name in CORE_NAMES:
        assert name in vars(pygkit), f"{name!r} should import eagerly"


def test_lazy_names_resolve_and_cache():
    assert pygkit.DialogBox is importlib.import_module("pygkit.ui").DialogBox
    assert pygkit.Inventory is importlib.import_module("pygkit.inventory").Inventory
    assert "DialogBox" in vars(pygkit)


def test_unknown_attribute():
    with pytest.raises(AttributeError):
        pygkit.NoSuchThing


def test_dir_sorted():
    assert pygkit.__dir__() == sorted(pygkit.__all__)


def _fresh_env():
    env = dict(os.environ)
    root = Path(__file__).parent.parent
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["SDL_VIDEODRIVER"] = "dummy"
    return env


def test_bare_import_stays_core():
    code = (
        "import sys, pygkit; "
        "loaded = {m.split('.')[1] for m in sys.modules if m.startswith('pygkit.')}; "
        "assert loaded <= {'signals', 'utils', 'protocols'}, sorted(loaded)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=_fresh_env()
    )
    assert proc.returncode == 0, proc.stderr


def test_submodule_from_import_fallback():
    code = (
        "import sys, pygkit; "
        "from pygkit import inventory; "
        "assert hasattr(inventory, 'InventoryWidget'); "
        "assert 'pygkit.ui' not in sys.modules"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=_fresh_env()
    )
    assert proc.returncode == 0, proc.stderr
