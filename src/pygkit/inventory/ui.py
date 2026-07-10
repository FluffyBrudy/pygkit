"""
Inventory UI rendering and interaction.

Provides the InventoryWidget class with grid-based rendering,
drag-and-drop support, tooltips, and visual feedback.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pygame
from pygame import SRCALPHA, Rect, Surface
from pygame.font import Font
from pygame.typing import ColorLike

from .assets import get_cache, render_quantity_text
from .core import Inventory
from .data import DEFAULT_INVENTORY_CONFIG, RARITY_COLORS, InventoryConfig, ItemStack


class Tooltip:
    """
    Tooltip display for item information.

    Shows item name, description, quantity, and stats on hover.
    """

    def __init__(
        self,
        font: Optional[Font] = None,
        title_font: Optional[Font] = None,
        bg_color: ColorLike = (30, 30, 35, 240),
        text_color: ColorLike = (255, 255, 255, 255),
        title_color: ColorLike = (255, 220, 100, 255),
        border_color: ColorLike = (80, 80, 90, 255),
        padding: int = 8,
        max_width: int = 250,
    ) -> None:
        self.font = font or pygame.font.Font(None, 18)
        self.title_font = title_font or pygame.font.Font(None, 22)
        self.bg_color = bg_color
        self.text_color = text_color
        self.title_color = title_color
        self.border_color = border_color
        self.padding = padding
        self.max_width = max_width

        self._surface: Optional[Surface] = None
        self._visible = False
        self._position = (0, 0)

    def show(self, item_stack: ItemStack, position: Tuple[int, int]) -> None:
        """Show tooltip for an item at the given position."""
        self._surface = self._render_tooltip(item_stack)
        self._position = position
        self._visible = True

    def hide(self) -> None:
        """Hide the tooltip."""
        self._visible = False
        self._surface = None

    @property
    def visible(self) -> bool:
        return self._visible

    def _render_tooltip(self, item_stack: ItemStack) -> Surface:
        """Render tooltip content to a surface."""
        lines: List[Tuple[str, ColorLike]] = []

        rarity = item_stack.rarity
        title_color = RARITY_COLORS.get(rarity, self.title_color)
        lines.append((item_stack.name, title_color))

        if item_stack.description:
            lines.append(("", self.text_color))

            words = item_stack.description.split()
            current_line = ""
            for word in words:
                test = f"{current_line} {word}".strip()
                if self.font.size(test)[0] <= self.max_width - 2 * self.padding:
                    current_line = test
                else:
                    if current_line:
                        lines.append((current_line, self.text_color))
                    current_line = word
            if current_line:
                lines.append((current_line, self.text_color))

        lines.append(("", self.text_color))

        if item_stack.is_stackable() and item_stack.max_stack_size > 1:
            lines.append((f"Quantity: {item_stack.quantity}/{item_stack.max_stack_size}", (200, 200, 200, 255)))

        if item_stack.weight > 0:
            lines.append((f"Weight: {item_stack.weight:.1f}", (180, 180, 180, 255)))

        if item_stack.value > 0:
            lines.append((f"Value: {item_stack.value}", (255, 220, 100, 255)))

        if item_stack.tags:
            tags_str = ", ".join(item_stack.tags)
            lines.append((f"Tags: {tags_str}", (150, 150, 200, 255)))

        line_height = self.font.get_linesize()
        title_height = self.title_font.get_linesize()
        total_height = title_height + (len(lines) - 1) * line_height + 2 * self.padding
        total_width = self.max_width

        surf = Surface((total_width, total_height), SRCALPHA)
        surf.fill((0, 0, 0, 0))

        pygame.draw.rect(surf, self.bg_color, (0, 0, total_width, total_height), border_radius=4)

        pygame.draw.rect(surf, self.border_color, (0, 0, total_width, total_height), width=1, border_radius=4)

        y = self.padding

        title_text, title_clr = lines[0]
        title_surf = self.title_font.render(title_text, True, title_clr)
        surf.blit(title_surf, (self.padding, y))
        y += title_height

        for text, color in lines[1:]:
            if text:
                text_surf = self.font.render(text, True, color)
                surf.blit(text_surf, (self.padding, y))
            y += line_height

        return surf

    def render(self, screen: Surface) -> None:
        """Render the tooltip to the screen."""
        if not self._visible or self._surface is None:
            return

        x, y = self._position

        offset_x = 15
        offset_y = 15

        if x + offset_x + self._surface.get_width() > screen.get_width():
            offset_x = -self._surface.get_width() - 15
        if y + offset_y + self._surface.get_height() > screen.get_height():
            offset_y = -self._surface.get_height() - 15

        screen.blit(self._surface, (x + offset_x, y + offset_y))


class DragDropState:
    """Manages drag and drop operation state."""

    IDLE = "idle"
    DRAGGING = "dragging"

    def __init__(self) -> None:
        self.state = self.IDLE
        self.dragged_stack: Optional[ItemStack] = None
        self.source_slot: int = -1
        self.source_inventory: Optional[str] = None
        self.cursor_offset: Tuple[int, int] = (0, 0)
        self.split_mode: bool = False

    def start_drag(
        self,
        stack: ItemStack,
        slot_index: int,
        inventory_id: str,
        cursor_pos: Tuple[int, int],
        slot_rect: Rect,
        split: bool = False,
    ) -> None:
        """Start a drag operation."""
        self.state = self.DRAGGING
        self.source_slot = slot_index
        self.source_inventory = inventory_id
        self.split_mode = split

        if split and stack.quantity > 1:
            half_qty = (stack.quantity + 1) // 2
            self.dragged_stack = ItemStack(data=stack.data, quantity=half_qty)
        else:
            self.dragged_stack = stack.copy()

        center_x = slot_rect.centerx
        center_y = slot_rect.centery
        self.cursor_offset = (
            cursor_pos[0] - center_x,
            cursor_pos[1] - center_y,
        )

    def end_drag(self) -> None:
        """End the current drag operation."""
        self.state = self.IDLE
        self.dragged_stack = None
        self.source_slot = -1
        self.source_inventory = None
        self.split_mode = False

    @property
    def is_dragging(self) -> bool:
        return self.state == self.DRAGGING


class InventoryWidget:
    """
    Visual representation of an inventory with full interaction support.

    Features:
    - Grid-based slot layout with configurable size
    - Drag and drop item management
    - Right-click stack splitting
    - Hover highlights and tooltips
    - Visual feedback for invalid drops
    - Quantity display on stacked items
    - Integration with Inventory logic class

    Usage:
        inventory = Inventory("player", {"rows": 4, "cols": 6})
        widget = InventoryWidget(inventory, position=(100, 100))

        while running:
            events = pygame.event.get()
            widget.handle_events(events)
            widget.update(dt)
            widget.render(screen)
    """

    def __init__(
        self,
        inventory: Inventory,
        position: Tuple[int, int] = (0, 0),
        config: Optional[InventoryConfig] = None,
    ) -> None:
        self.inventory = inventory
        self.position = position
        self.config = {**DEFAULT_INVENTORY_CONFIG, **(config or {})}

        self.rows = inventory.rows
        self.cols = inventory.cols
        slot_size_cfg = self.config.get("slot_size", 48)
        gap_cfg = self.config.get("gap", 4)

        self.slot_size = slot_size_cfg if isinstance(slot_size_cfg, tuple) else (slot_size_cfg, slot_size_cfg)
        self.gap = gap_cfg if isinstance(gap_cfg, tuple) else (gap_cfg, gap_cfg)

        self.total_width = self.cols * self.slot_size[0] + (self.cols - 1) * self.gap[0]
        self.total_height = self.rows * self.slot_size[1] + (self.rows - 1) * self.gap[1]

        self.padding = 10

        self.panel_width = self.total_width + 2 * self.padding
        self.panel_height = self.total_height + 2 * self.padding

        self.quantity_font = pygame.font.Font(None, 20)
        self.tooltip_font = pygame.font.Font(None, 18)
        self.tooltip_title_font = pygame.font.Font(None, 22)

        self._hovered_slot: Optional[int] = None
        self._tooltip_timer: float = 0.0
        self._tooltip_delay = self.config.get("tooltip_delay", 300) / 1000.0

        self._drag_state = DragDropState()

        self._tooltip = Tooltip(
            font=self.tooltip_font,
            title_font=self.tooltip_title_font,
        )

        self._cache = get_cache()

        self._slot_bg_default = self._cache.get_slot_surface(
            self.slot_size,
            self.config.get("border_radius", 4),
            "default",
        )
        self._slot_bg_highlight = self._cache.get_slot_surface(
            self.slot_size,
            self.config.get("border_radius", 4),
            "highlighted",
        )
        self._slot_bg_invalid = self._cache.get_slot_surface(
            self.slot_size,
            self.config.get("border_radius", 4),
            "invalid",
        )

    def get_slot_rect(self, slot_index: int) -> Rect:
        """Get the screen rectangle for a specific slot."""
        row = slot_index // self.cols
        col = slot_index % self.cols

        x = self.position[0] + self.padding + col * (self.slot_size[0] + self.gap[0])
        y = self.position[1] + self.padding + row * (self.slot_size[1] + self.gap[1])

        return Rect(x, y, *self.slot_size)

    def get_slot_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get the slot index at a given screen position, or None if outside grid."""
        x, y = pos

        panel_rect = Rect(
            self.position[0],
            self.position[1],
            self.panel_width,
            self.panel_height,
        )

        if not panel_rect.collidepoint(x, y):
            return None

        grid_x = x - self.position[0] - self.padding
        grid_y = y - self.position[1] - self.padding

        if grid_x < 0 or grid_y < 0:
            return None

        col = grid_x // (self.slot_size[0] + self.gap[0])
        row = grid_y // (self.slot_size[1] + self.gap[1])

        if 0 <= col < self.cols and 0 <= row < self.rows:
            return row * self.cols + col

        return None

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """Process pygame events for inventory interaction."""
        mouse_pos = pygame.mouse.get_pos()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_left_click(mouse_pos)
                elif event.button == 3:
                    self._handle_right_click(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self._handle_left_release(mouse_pos)

    def _handle_mouse_motion(self, pos: Tuple[int, int]) -> None:
        """Handle mouse movement for hover effects."""
        slot = self.get_slot_at_position(pos)

        if self._drag_state.is_dragging:
            pass

        if slot != self._hovered_slot:
            self._hovered_slot = slot
            self._tooltip_timer = 0.0
            self._tooltip.hide()

    def _handle_left_click(self, pos: Tuple[int, int]) -> None:
        """Handle left mouse button press."""
        slot = self.get_slot_at_position(pos)

        if slot is None:
            return

        stack = self.inventory.get_slot(slot)

        if stack is None:
            return

        slot_rect = self.get_slot_rect(slot)
        self._drag_state.start_drag(
            stack,
            slot,
            self.inventory.inventory_id,
            pos,
            slot_rect,
            split=False,
        )

    def _handle_right_click(self, pos: Tuple[int, int]) -> None:
        """Handle right mouse button press for stack splitting."""
        if not self.config.get("allow_right_click_split", True):
            return

        slot = self.get_slot_at_position(pos)

        if slot is None:
            return

        stack = self.inventory.get_slot(slot)

        if stack is None or not stack.is_stackable() or stack.quantity < 2:
            return

        slot_rect = self.get_slot_rect(slot)
        self._drag_state.start_drag(
            stack,
            slot,
            self.inventory.inventory_id,
            pos,
            slot_rect,
            split=True,
        )

    def _handle_left_release(self, pos: Tuple[int, int]) -> None:
        """Handle left mouse button release to complete drag operation."""
        if not self._drag_state.is_dragging:
            return

        target_slot = self.get_slot_at_position(pos)

        if target_slot is not None:
            self._attempt_drop(target_slot)

        self._drag_state.end_drag()

    def _attempt_drop(self, target_slot: int) -> bool:
        """
        Attempt to drop dragged item into target slot.

        Returns True if drop was successful.
        """
        source_slot = self._drag_state.source_slot
        dragged_stack = self._drag_state.dragged_stack

        if dragged_stack is None:
            return False

        if target_slot == source_slot:
            return False

        target_stack = self.inventory.get_slot(target_slot)

        if target_stack and dragged_stack.can_stack_with(target_stack):
            space = target_stack.max_stack_size - target_stack.quantity

            if self._drag_state.split_mode:
                to_move = min(dragged_stack.quantity, space)
                if to_move > 0:
                    target_stack.add_quantity(to_move)
                    dragged_stack.remove_quantity(to_move)

                    if dragged_stack.quantity <= 0:
                        self.inventory.remove_from_slot(source_slot)

                    return True
            else:
                to_move = min(dragged_stack.quantity, space)
                if to_move > 0:
                    if to_move >= dragged_stack.quantity:
                        self.inventory.move_item(source_slot, target_slot)
                        return True
                    else:
                        target_stack.add_quantity(to_move)
                        dragged_stack.remove_quantity(to_move)
                        self.inventory.remove_from_slot(source_slot, dragged_stack.quantity)
                        return True

        elif target_stack is None:
            if self._drag_state.split_mode:
                new_stack = self.inventory.split_stack(source_slot, dragged_stack.quantity)
                return new_stack is not None
            else:
                return self.inventory.move_item(source_slot, target_slot)

        if self.config.get("allow_stack_swap", True) and not self._drag_state.split_mode:
            return self.inventory.move_item(source_slot, target_slot)

        return False

    def update(self, dt: float) -> None:
        """Update inventory state (tooltip timing, etc.)."""
        if self._hovered_slot is not None and not self._drag_state.is_dragging:
            stack = self.inventory.get_slot(self._hovered_slot)
            if stack:
                self._tooltip_timer += dt
                if self._tooltip_timer >= self._tooltip_delay:
                    if not self._tooltip.visible:
                        mouse_pos = pygame.mouse.get_pos()
                        self._tooltip.show(stack, mouse_pos)
            else:
                self._tooltip.hide()
                self._tooltip_timer = 0.0
        else:
            self._tooltip_timer = 0.0
            self._tooltip.hide()

    def render(self, screen: Surface) -> None:
        """Render the inventory UI to the screen."""

        bg_color = self.config.get("background_color", (40, 40, 45, 230))
        border_color = self.config.get("border_color", (100, 100, 110, 255))
        border_radius = self.config.get("border_radius", 6)
        border_width = self.config.get("border_width", 2)

        panel_rect = Rect(
            self.position[0],
            self.position[1],
            self.panel_width,
            self.panel_height,
        )

        pygame.draw.rect(
            screen,
            bg_color,
            panel_rect,
            border_radius=border_radius,
        )

        pygame.draw.rect(
            screen,
            border_color,
            panel_rect,
            width=border_width,
            border_radius=border_radius,
        )

        for i in range(self.inventory.total_slots):
            slot_rect = self.get_slot_rect(i)
            stack = self.inventory.get_slot(i)

            if self._drag_state.is_dragging and i == self._hovered_slot:
                is_valid = self._is_valid_drop_target(i)
                bg_surface = self._slot_bg_highlight if is_valid else self._slot_bg_invalid
            elif i == self._hovered_slot and not self._drag_state.is_dragging:
                bg_surface = self._slot_bg_highlight
            else:
                bg_surface = self._slot_bg_default

            screen.blit(bg_surface, slot_rect.topleft)

            if stack:
                icon = self._cache.get_icon_surface(
                    stack.icon_shape,
                    (self.slot_size[0] - 8, self.slot_size[1] - 8),
                    stack.icon_color,
                )

                icon_x = slot_rect.centerx - icon.get_width() // 2
                icon_y = slot_rect.centery - icon.get_height() // 2
                screen.blit(icon, (icon_x, icon_y))

                if stack.quantity > 1:
                    qty_surface = render_quantity_text(
                        stack.quantity,
                        self.quantity_font,
                    )
                    qty_x = slot_rect.right - qty_surface.get_width() - 2
                    qty_y = slot_rect.bottom - qty_surface.get_height() - 2
                    screen.blit(qty_surface, (qty_x, qty_y))

        if self._drag_state.is_dragging and self._drag_state.dragged_stack:
            dragged = self._drag_state.dragged_stack
            mouse_pos = pygame.mouse.get_pos()

            icon = self._cache.get_icon_surface(
                dragged.icon_shape,
                (self.slot_size[0] - 8, self.slot_size[1] - 8),
                dragged.icon_color,
            )

            icon_x = mouse_pos[0] - icon.get_width() // 2
            icon_y = mouse_pos[1] - icon.get_height() // 2

            screen.blit(icon, (icon_x, icon_y))

            if dragged.quantity > 1:
                qty_surface = render_quantity_text(
                    dragged.quantity,
                    self.quantity_font,
                )
                screen.blit(
                    qty_surface,
                    (
                        icon_x + icon.get_width() - qty_surface.get_width(),
                        icon_y + icon.get_height() - qty_surface.get_height(),
                    ),
                )

        self._tooltip.render(screen)

    def _is_valid_drop_target(self, slot_index: int) -> bool:
        """Check if a slot is a valid drop target for the currently dragged item."""
        if not self._drag_state.is_dragging:
            return False

        dragged = self._drag_state.dragged_stack
        if dragged is None:
            return False

        target = self.inventory.get_slot(slot_index)

        if target is None:
            return True

        if dragged.can_stack_with(target):
            space = target.max_stack_size - target.quantity
            return space > 0

        return self.config.get("allow_stack_swap", True)

    def set_position(self, pos: Tuple[int, int]) -> None:
        """Move the inventory widget to a new position."""
        self.position = pos

    def toggle_visibility(self) -> None:
        """Toggle inventory visibility (to be handled by parent manager)."""
        pass


class InventoryManager:
    """
    Manages multiple inventory widgets and coordinates interactions.

    Handles:
    - Opening/closing inventories
    - Multiple inventory support (player, chest, shop)
    - Global input routing
    - Transition animations
    """

    def __init__(self) -> None:
        self._inventories: Dict[str, InventoryWidget] = {}
        self._active_inventories: List[str] = []
        self._visible = False

    def register_inventory(
        self,
        inventory: Inventory,
        widget: InventoryWidget,
        inventory_id: Optional[str] = None,
    ) -> None:
        """Register an inventory widget for management."""
        inv_id = inventory_id or inventory.inventory_id
        self._inventories[inv_id] = widget

    def open_inventory(self, inventory_id: str) -> None:
        """Open/show an inventory."""
        if inventory_id in self._inventories:
            if inventory_id not in self._active_inventories:
                self._active_inventories.append(inventory_id)
            self._visible = True

    def close_inventory(self, inventory_id: str) -> None:
        """Close/hide an inventory."""
        if inventory_id in self._active_inventories:
            self._active_inventories.remove(inventory_id)

        if not self._active_inventories:
            self._visible = False

    def close_all(self) -> None:
        """Close all open inventories."""
        self._active_inventories.clear()
        self._visible = False

    def toggle_inventory(self, inventory_id: str) -> None:
        """Toggle an inventory's open/closed state."""
        if inventory_id in self._active_inventories:
            self.close_inventory(inventory_id)
        else:
            self.open_inventory(inventory_id)

    @property
    def is_visible(self) -> bool:
        return self._visible

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        """Route events to active inventories."""
        if not self._visible:
            return

        for inv_id in self._active_inventories:
            if inv_id in self._inventories:
                self._inventories[inv_id].handle_events(events)

    def update(self, dt: float) -> None:
        """Update all active inventories."""
        if not self._visible:
            return

        for inv_id in self._active_inventories:
            if inv_id in self._inventories:
                self._inventories[inv_id].update(dt)

    def render(self, screen: Surface) -> None:
        """Render all active inventories."""
        if not self._visible:
            return

        for inv_id in self._active_inventories:
            if inv_id in self._inventories:
                self._inventories[inv_id].render(screen)
