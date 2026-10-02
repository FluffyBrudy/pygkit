import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import time

import pygame
import pytest

from pygkit.audio import SFX_CHANNELS, SoundManager

TOL = 0.02


def silence(seconds=0.1):
    freq, size, channels = pygame.mixer.get_init()
    frames = max(1, int(freq * seconds))
    return pygame.mixer.Sound(buffer=b"\x00" * (frames * abs(size) // 8 * channels))


@pytest.fixture
def mgr():
    return SoundManager()


@pytest.fixture
def blip(mgr):
    mgr._sfx["blip"] = silence()
    return "blip"


@pytest.fixture
def music(mgr):
    mgr._main["music"] = silence(seconds=0.5)
    return "music"


def test_play_returns_channel(mgr, blip):
    ch = mgr.play(blip)
    assert isinstance(ch, pygame.mixer.Channel)
    assert ch.get_busy()


def test_unknown_key(mgr):
    with pytest.raises(KeyError):
        mgr.play("nope")
    with pytest.raises(KeyError):
        mgr.playing("nope")
    with pytest.raises(KeyError):
        mgr.channel_for("nope")
    with pytest.raises(KeyError):
        mgr.set_volume(0.5, kind="sfx", key="nope")


def test_channel_for_and_playing(mgr, blip):
    assert mgr.channel_for(blip) is None
    assert mgr.playing(blip) is False
    ch = mgr.play(blip, loops=-1)
    found = mgr.channel_for(blip)
    assert found is not None and found.get_sound() is mgr._sfx[blip]
    assert mgr.playing(blip) is True
    ch.stop()
    assert mgr.channel_for(blip) is None
    assert mgr.playing(blip) is False


def test_expiry_without_stop(mgr):
    mgr._sfx["tick"] = silence(seconds=0.05)
    mgr.play("tick")
    assert mgr.playing("tick") is True
    time.sleep(0.4)
    assert mgr.playing("tick") is False
    assert mgr.channel_for("tick") is None


def test_stop_scopes(mgr, blip, music):
    mgr.play(blip, loops=-1)
    mgr.play(music, kind="main")
    mgr.stop(kind="sfx")
    assert mgr.playing(blip) is False
    assert mgr.playing(music, kind="main") is True
    mgr.stop(kind="sfx", key=blip)
    mgr.stop(kind="main", key=music)
    assert mgr.playing(music, kind="main") is False
    with pytest.raises(ValueError):
        mgr.stop()
    with pytest.raises(ValueError):
        mgr.stop(key=blip)


def test_volume_layers(mgr, blip):
    mgr.set_volume(0.5)
    mgr.set_volume(0.5, kind="sfx")
    mgr._vol[("sfx", blip)] = 0.5
    ch = mgr.play(blip, loops=-1)
    assert abs(ch.get_volume() - 0.125) < TOL
    mgr.set_volume(0.5, kind="sfx", key=blip)
    assert abs(mgr.get_volume(kind="sfx", key=blip) - 0.5) < TOL
    assert mgr.get_volume() == 0.5
    assert mgr.get_volume(kind="sfx") == 0.5


def test_volume_live_apply(mgr, blip):
    ch = mgr.play(blip, loops=-1)
    assert abs(ch.get_volume() - 1.0) < TOL
    mgr.set_volume(0.0, kind="sfx")
    assert ch.get_volume() == 0.0
    mgr.set_volume(0.5, kind="sfx")
    assert abs(ch.get_volume() - 0.5) < TOL
    mgr.set_volume(0.5)
    assert abs(ch.get_volume() - 0.25) < TOL


def test_volume_clamped(mgr, blip):
    mgr.set_volume(2.0, kind="sfx", key=blip)
    assert mgr.get_volume(kind="sfx", key=blip) == 1.0
    mgr.set_volume(-1.0)
    assert mgr.get_volume() == 0.0
    with pytest.raises(ValueError):
        mgr.set_volume(0.5, key=blip)
    with pytest.raises(ValueError):
        mgr.get_volume(key=blip)


def test_play_volume_kwarg(mgr, blip):
    ch = mgr.play(blip, loops=-1, volume=0.25)
    assert abs(ch.get_volume() - 0.25) < TOL
    assert abs(mgr.get_volume(kind="sfx", key=blip) - 0.25) < TOL
    ch2 = mgr.play(blip, loops=-1)
    assert abs(ch2.get_volume() - 0.25) < TOL
    ch.stop()
    ch2.stop()


def test_steal_resets_volume(mgr):
    keys = []
    for i in range(SFX_CHANNELS + 1):
        key = f"s{i}"
        mgr._sfx[key] = silence(seconds=1.0)
        keys.append(key)
    mgr.set_volume(0.1, kind="sfx", key=keys[0])
    first = mgr.play(keys[0], loops=-1)
    assert abs(first.get_volume() - 0.1) < TOL
    for key in keys[1:]:
        mgr.set_volume(0.9, kind="sfx", key=key)
        mgr.play(key, loops=-1)
    assert abs(first.get_volume() - 0.9) < TOL
    assert mgr.channel_for(keys[0]) is None


def test_channel_id_path(mgr, blip):
    ch = mgr.play(blip, loops=-1, channel_id=2, volume=0.4)
    assert ch is mgr.get_channel(2)
    assert abs(ch.get_volume() - 0.4) < TOL


def test_fadeout(mgr, blip):
    mgr.play(blip, loops=-1)
    mgr.fadeout(100, kind="sfx", key=blip)
    time.sleep(0.4)
    assert mgr.playing(blip) is False
    with pytest.raises(ValueError):
        mgr.fadeout(100, key=blip)


def test_add_sound_missing_file(mgr, tmp_path):
    assert mgr.add_sound(tmp_path / "nope.wav", "x") is False


def test_mixer_grows_to_num_channels():
    mgr = SoundManager(num_channels=16)
    assert len(mgr._channels) == 16
    import pygame as _pg

    assert _pg.mixer.get_num_channels() >= 16
    mgr.stop_all()


def test_stop_key_stops_every_copy(mgr):
    mgr._sfx["hum"] = silence(seconds=1.0)
    first = mgr.play("hum", loops=-1)
    second = mgr.play("hum", loops=-1)
    assert first is not second
    assert len(mgr.channels_for("hum")) == 2
    mgr.stop(kind="sfx", key="hum")
    assert mgr.playing("hum") is False


def test_channel_id_out_of_range(mgr, blip):
    with pytest.raises(ValueError):
        mgr.play(blip, channel_id=999)
    with pytest.raises(ValueError):
        mgr.get_channel(-1)


def test_unknown_kind_rejected(mgr, blip):
    with pytest.raises(ValueError):
        mgr.play(blip, kind="music")
    with pytest.raises(KeyError):
        mgr.get_volume(kind="sfx", key="nope")
