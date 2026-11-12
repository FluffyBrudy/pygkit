from typing import Any, Callable, List, TypedDict

import pygame
from pygame import SRCALPHA, Surface
from pygame.typing import ColorLike


class BoxModel(TypedDict, total=False):
    margin_x: int
    margin_y: int
    padding_x: int
    padding_y: int
    width: int
    height: int
    border_width: int


class BoxModelResult(TypedDict, total=True):
    left: int
    top: int
    offset_x: int
    offset_y: int
    full_width: int
    full_height: int
    content_width: int
    content_height: int


class UIOptions(BoxModel, total=False):
    border_radius: int
    border_color: ColorLike
    background: ColorLike
    fill_color: ColorLike


def generate_box_model(model: BoxModel) -> BoxModelResult:
    width = model.get("width", 0)
    height = model.get("height", 0)
    padding_x = model.get("padding_x", 0)
    padding_y = model.get("padding_y", 0)
    margin_x = model.get("margin_x", 0)
    margin_y = model.get("margin_y", 0)
    border_width = model.get("border_width", 0)

    inner_x = 2 * (padding_x + border_width)
    inner_y = 2 * (padding_y + border_width)

    return {
        "left": padding_x + border_width,
        "top": padding_y + border_width,
        "offset_x": margin_x,
        "offset_y": margin_y,
        "full_width": width,
        "full_height": height,
        "content_width": width - inner_x,
        "content_height": height - inner_y,
    }


class UIBase:
    def __init__(self, options: UIOptions) -> None:
        self.colors: dict[str, ColorLike] = {
            "bg": options.get("background", (0, 0, 0, 0))
        }

        self.box_model = generate_box_model(options)

        self.border: dict[str, Any] = {
            "radius": options.get("border_radius", 0),
            "width": options.get("border_width", 0),
            "color": options.get("border_color", (0, 0, 0, 0)),
        }

        local_size = self.box_model["full_width"], self.box_model["full_height"]
        self.local_surface = Surface(local_size, SRCALPHA)

        self.renderable_plugins: List[Callable[[Surface], Any]] = []

    def add_plugin(self, cb: Callable[[Surface], Any]) -> None:
        self.renderable_plugins.append(cb)

    def draw_base(self) -> None:
        local_surf = self.local_surface
        local_surf.fill((0, 0, 0, 0))

        bg_color = self.colors["bg"]
        border_width = self.border["width"]
        border_radius = self.border["radius"]
        border_color = self.border["color"]

        content_pos = self.box_model["left"], self.box_model["top"]
        content_size = self.box_model["content_width"], self.box_model["content_height"]
        surface_size = local_surf.get_size()

        if border_width > 0:
            pygame.draw.rect(
                local_surf,
                border_color,
                (0, 0, *surface_size),
                width=border_width,
                border_radius=border_radius,
            )

        pygame.draw.rect(
            local_surf,
            bg_color,
            (*content_pos, *content_size),
            border_radius=max(0, border_radius - border_width),
        )

    @property
    def size(self) -> tuple[int, int]:
        return (self.box_model["full_width"], self.box_model["full_height"])

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        self.draw_base()
        for plugin in self.renderable_plugins:
            plugin(self.local_surface)
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        screen.blit(self.local_surface, pos)

    def update(self) -> None:
        pass
