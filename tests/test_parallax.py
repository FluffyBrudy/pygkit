import pygame
import pytest

from pygkit.parallax import Camera2D, ParallaxBackground, ParallaxLayer


def stripe(w, h, color):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(color)
    for x in range(0, w, 8):
        s.fill((255, 255, 255, 255), (x, 0, 2, h))
    return s


class TestParallaxLayer:
    def test_factor_number_applies_to_x(self):
        assert ParallaxLayer(stripe(40, 40, (1, 2, 3, 255)), factor=0.5).factor == (0.5, 0.0)

    def test_factor_pair(self):
        layer = ParallaxLayer(stripe(40, 40, (1, 2, 3, 255)), factor=(0.5, 0.25))
        assert layer.factor == (0.5, 0.25)

    def test_factor_above_one_and_negative(self):
        img = stripe(40, 40, (1, 2, 3, 255))
        assert ParallaxLayer(img, factor=2.0).factor == (2.0, 0.0)
        assert ParallaxLayer(img, factor=-0.5).factor == (-0.5, 0.0)

    def test_defaults(self):
        layer = ParallaxLayer(stripe(40, 40, (1, 2, 3, 255)))
        assert layer.factor == (0.0, 0.0)
        assert layer.x_mode == "tile"
        assert layer.y_mode == "clamp"
        assert layer.anchor == "bottom"

    def test_invalid_inputs_rejected(self):
        img = stripe(40, 40, (1, 2, 3, 255))
        for kwargs in (
            {"x_mode": "wrap"},
            {"y_mode": "nope"},
            {"anchor": "middle"},
            {"scale": 0},
            {"scale": 1.5},
            {"scale": True},
            {"offset": 5},
            {"factor": float("nan")},
            {"factor": (0.5, float("inf"))},
        ):
            with pytest.raises(ValueError):
                ParallaxLayer(img, **kwargs)
        with pytest.raises(ValueError):
            ParallaxLayer(None)

    def test_scale_prescales(self):
        layer = ParallaxLayer(stripe(20, 10, (1, 2, 3, 255)), scale=2)
        assert layer.image.get_size() == (40, 20)


class TestParallaxBackground:
    def test_x_tile_seamless(self):
        bg = ParallaxBackground([ParallaxLayer(stripe(37, 40, (200, 40, 40, 255)), factor=(0.5, 0.0))])
        a = pygame.Surface((200, 40))
        b = pygame.Surface((200, 40))
        bg.render(a, 0, 0)
        bg.render(b, 37 * 2 * 10, 0)
        for x in range(200):
            for y in range(40):
                assert a.get_at((x, y)) == b.get_at((x, y))

    def test_tile_matches_long_reference(self):
        img = stripe(37, 40, (40, 200, 40, 255))
        bg = ParallaxBackground([ParallaxLayer(img, factor=(1.0, 0.0))])
        long_img = pygame.Surface((37 * 8, 40), pygame.SRCALPHA)
        for i in range(8):
            long_img.blit(img, (i * 37, 0))
        ref = pygame.Surface((200, 40))
        ref.blit(long_img, (-53, 0))
        got = pygame.Surface((200, 40))
        bg.render(got, 53, 0)
        for x in range(200):
            for y in range(40):
                assert got.get_at((x, y)) == ref.get_at((x, y))

    def test_y_tile_seamless(self):
        bg = ParallaxBackground([ParallaxLayer(stripe(50, 33, (40, 40, 200, 255)), factor=(0.0, 0.5), y_mode="tile")])
        a = pygame.Surface((50, 120))
        b = pygame.Surface((50, 120))
        bg.render(a, 0, 0)
        bg.render(b, 0, 33 * 2 * 6)
        for x in range(50):
            for y in range(120):
                assert a.get_at((x, y)) == b.get_at((x, y))

    def test_clamp_anchors(self):
        short = stripe(50, 60, (9, 9, 9, 255))
        top = pygame.Surface((50, 120))
        ParallaxBackground(
            [ParallaxLayer(short, factor=(0, 0), y_mode="clamp", anchor="top")]
        ).render(top, 0, 0)
        assert top.get_at((27, 5))[:3] == (9, 9, 9)
        assert top.get_at((27, 119))[:3] == (0, 0, 0)
        bottom = pygame.Surface((50, 120))
        ParallaxBackground(
            [ParallaxLayer(short, factor=(0, 0), y_mode="clamp", anchor="bottom")]
        ).render(bottom, 0, 0)
        assert bottom.get_at((27, 119))[:3] == (9, 9, 9)
        assert bottom.get_at((27, 5))[:3] == (0, 0, 0)
        center = pygame.Surface((50, 120))
        ParallaxBackground(
            [ParallaxLayer(short, factor=(0, 0), y_mode="clamp", anchor="center")]
        ).render(center, 0, 0)
        assert center.get_at((27, 60))[:3] == (9, 9, 9)
        assert center.get_at((27, 5))[:3] == (0, 0, 0)

    def test_clamp_pans_when_wider(self):
        wide = stripe(300, 40, (9, 9, 9, 255))
        bg = ParallaxBackground([ParallaxLayer(wide, factor=(1.0, 0.0), x_mode="clamp")])
        a = pygame.Surface((200, 40))
        b = pygame.Surface((200, 40))
        bg.render(a, 0, 0)
        bg.render(b, 10000, 0)
        assert a.get_at((0, 5)) != b.get_at((0, 5))
        c = pygame.Surface((200, 40))
        d = pygame.Surface((200, 40))
        bg.render(c, 10000, 0)
        bg.render(d, 20000, 0)
        for x in range(200):
            assert c.get_at((x, 5)) == d.get_at((x, 5))

    def test_once_positioning(self):
        img = stripe(40, 40, (200, 200, 40, 255))
        fixed = ParallaxBackground([ParallaxLayer(img, factor=(0.0, 0.0), x_mode="once", y_mode="once")])
        s = pygame.Surface((200, 40))
        fixed.render(s, 5000, 0)
        assert s.get_at((5, 5))[:3] == (200, 200, 40)
        world = ParallaxBackground([ParallaxLayer(img, factor=(1.0, 0.0), x_mode="once", y_mode="once")])
        s2 = pygame.Surface((200, 40))
        world.render(s2, 0, 0)
        assert s2.get_at((5, 5))[:3] == (200, 200, 40)
        s3 = pygame.Surface((200, 40))
        world.render(s3, 5000, 0)
        assert s3.get_at((5, 5))[:3] != (200, 200, 40)

    def test_offset_shifts_once_position(self):
        img = stripe(40, 40, (200, 200, 40, 255))
        bg = ParallaxBackground(
            [ParallaxLayer(img, factor=(0.0, 0.0), x_mode="once", y_mode="once", offset=(80, 0))]
        )
        s = pygame.Surface((200, 40))
        bg.render(s, 0, 0)
        assert s.get_at((5, 5))[:3] == (0, 0, 0)
        assert s.get_at((85, 5))[:3] == (200, 200, 40)

    def test_add_remove_len(self):
        bg = ParallaxBackground()
        assert len(bg) == 0
        layer = ParallaxLayer(stripe(40, 40, (1, 2, 3, 255)))
        bg.add(layer)
        assert len(bg) == 1
        assert bg.remove(layer) is True
        assert bg.remove(layer) is False
        assert len(bg) == 0


class TestCamera2D:
    def test_follow_snaps_centered(self):
        class Dot:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        cam = Camera2D(100, 100)
        cam.follow(Dot(500, 300))
        cam.update(0.016)
        assert (cam.x, cam.y) == (450.0, 250.0)

    def test_follow_at(self):
        cam = Camera2D(100, 100)
        cam.follow_at(1000, 1000)
        cam.update(0.016)
        assert (cam.x, cam.y) == (950.0, 950.0)

    def test_lerp_smoothing(self):
        class Dot:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        cam = Camera2D(100, 100)
        cam.lerp_speed = 5.0
        cam.follow(Dot(500, 300))
        cam.update(0.016)
        assert 0.0 < cam.x < 450.0
        assert 0.0 < cam.y < 250.0

    def test_bounds_clamp(self):
        class Dot:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        cam = Camera2D(100, 100)
        cam.follow(Dot(500, 300))
        cam.update(0.016)
        cam.set_bounds(0, 0, 200, 200)
        cam.update(0.016)
        assert (cam.x, cam.y) == (100.0, 100.0)

    def test_bounds_smaller_than_viewport_centers(self):
        cam = Camera2D(100, 100)
        cam.set_bounds(0, 0, 60, 60)
        cam.update(0.016)
        assert (cam.x, cam.y) == (-20.0, -20.0)

    def test_invalid_bounds_rejected(self):
        cam = Camera2D(100, 100)
        with pytest.raises(ValueError):
            cam.set_bounds(10, 0, 5, 5)

    def test_deadzone_holds_inside(self):
        class Dot:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        cam = Camera2D(200, 200, mode="deadzone")
        cam.follow(Dot(100, 100))
        cam.update(0.016)
        assert (cam.x, cam.y) == (0.0, 0.0)
        cam.follow(Dot(400, 100))
        cam.update(0.016)
        assert cam.x > 0.0

    def test_bad_mode_rejected(self):
        with pytest.raises(ValueError):
            Camera2D(100, 100, mode="follow")

    def test_shake_decays(self):
        cam = Camera2D(100, 100)
        cam.shake(0.3, 8.0)
        cam.update(0.1)
        cam.update(1.0)
        assert cam.offset == (cam.x, cam.y)

    def test_shake_bad_args_rejected(self):
        cam = Camera2D(100, 100)
        with pytest.raises(ValueError):
            cam.shake(-1, 1.0)
        with pytest.raises(ValueError):
            cam.shake(1.0, -1.0)

    def test_velocity_drifts_without_target(self):
        cam = Camera2D(100, 100)
        cam.velocity = (90.0, 60.0)
        cam.update(1.0)
        assert (cam.x, cam.y) == (90.0, 60.0)

    def test_velocity_ignored_while_following(self):
        class Dot:
            def __init__(self, x, y):
                self.x = x
                self.y = y

        cam = Camera2D(100, 100)
        cam.velocity = (90.0, 60.0)
        cam.follow(Dot(500, 300))
        cam.update(1.0)
        assert (cam.x, cam.y) == (450.0, 250.0)

    def test_velocity_bad_value_rejected(self):
        cam = Camera2D(100, 100)
        for bad in ("fast", (1.0,), (float("nan"), 0.0)):
            with pytest.raises((ValueError, TypeError)):
                cam.velocity = bad

    def test_bad_dt_ignored(self):
        cam = Camera2D(100, 100)
        cam.velocity = (90.0, 60.0)
        cam.update(float("nan"))
        cam.update(-1.0)
        assert (cam.x, cam.y) == (0.0, 0.0)
