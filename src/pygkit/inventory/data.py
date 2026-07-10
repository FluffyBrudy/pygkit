"""
Data structures for the Inventory System.

Provides type-safe definitions for items, inventory configuration,
and related data structures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Literal, Optional, TypedDict, Union

from pygame.typing import ColorLike


class ItemData(TypedDict, total=False):
    """
    Flexible item definition with required core fields and optional metadata.

    Required:
        id: Unique string identifier (e.g., "potion_health_small")
        name: Display name (e.g., "Small Health Potion")

    Optional:
        description: Item description for tooltips
        icon_color: RGBA color for procedural icon generation
        icon_shape: Shape type for icon ("circle", "square", "diamond", "cross")
        stack_size: Maximum stack size (default: 1 for unique items)
        quantity: Current stack quantity (used when adding to inventory)
        tags: List of tags for filtering/categorization (e.g., ["consumable", "healing"])
        rarity: Rarity tier ("common", "uncommon", "rare", "epic", "legendary")
        metadata: Arbitrary additional data for game-specific logic
        weight: Item weight for encumbrance systems
        value: Item value for trading systems
        use_callback: Optional callback when item is used
    """

    id: str
    name: str
    description: str
    icon_color: ColorLike
    icon_shape: Literal["circle", "square", "diamond", "cross", "star"]
    stack_size: int
    quantity: int
    tags: List[str]
    rarity: Literal["common", "uncommon", "rare", "epic", "legendary"]
    metadata: dict[str, Any]
    weight: float
    value: int
    use_callback: Optional[Callable[[], None]]


class InventoryConfig(TypedDict, total=False):
    """
    Configuration for inventory container behavior and appearance.

    Layout:
        rows: Number of rows in grid
        cols: Number of columns in grid
        slot_size: Size of each slot in pixels (width, height) or single int
        gap: Gap between slots in pixels (x, y) or single int

    Behavior:
        allow_drag_drop: Enable drag and drop interactions
        allow_right_click_split: Enable right-click to split stacks
        allow_stack_swap: Allow swapping items between slots
        max_weight: Maximum total weight (None = unlimited)
        auto_stack: Automatically stack identical items

    Appearance:
        background_color: Background color for inventory panel
        slot_empty_color: Color for empty slots
        slot_filled_color: Color for filled slots
        slot_highlight_color: Color for hovered/dragged slots
        border_color: Border color for inventory panel
        border_radius: Border radius for rounded corners
        border_width: Width of border
        tooltip_enabled: Show tooltips on hover
        tooltip_delay: Delay before tooltip appears (milliseconds)
    """

    rows: int
    cols: int
    slot_size: Union[int, tuple[int, int]]
    gap: Union[int, tuple[int, int]]

    allow_drag_drop: bool
    allow_right_click_split: bool
    allow_stack_swap: bool
    max_weight: Optional[float]
    auto_stack: bool

    background_color: ColorLike
    slot_empty_color: ColorLike
    slot_filled_color: ColorLike
    slot_highlight_color: ColorLike
    slot_invalid_color: ColorLike
    border_color: ColorLike
    border_radius: int
    border_width: int
    tooltip_enabled: bool
    tooltip_delay: int


@dataclass
class ItemStack:
    """
    Represents a stack of items in the inventory.

    Wraps ItemData with quantity tracking and validation.
    """

    data: dict[str, Any]
    quantity: int = 1

    @property
    def id(self) -> str:
        return self.data.get("id", "")

    @property
    def name(self) -> str:
        return self.data.get("name", "Unknown Item")

    @property
    def description(self) -> str:
        return self.data.get("description", "")

    @property
    def max_stack_size(self) -> int:
        return self.data.get("stack_size", 1)

    @property
    def weight(self) -> float:
        base_weight = self.data.get("weight", 0.0)
        return base_weight * self.quantity

    @property
    def value(self) -> int:
        base_value = self.data.get("value", 0)
        return base_value * self.quantity

    @property
    def tags(self) -> list[str]:
        return self.data.get("tags", [])

    @property
    def rarity(self) -> str:
        return self.data.get("rarity", "common")

    @property
    def icon_color(self) -> ColorLike:
        return self.data.get("icon_color", (200, 200, 200, 255))

    @property
    def icon_shape(self) -> str:
        return self.data.get("icon_shape", "circle")

    @property
    def metadata(self) -> dict[str, Any]:
        return self.data.get("metadata", {})

    def is_stackable(self) -> bool:
        """Check if this item can be stacked."""
        return self.max_stack_size > 1

    def can_stack_with(self, other: ItemStack) -> bool:
        """Check if this stack can be combined with another."""
        if not self.is_stackable() or not other.is_stackable():
            return False
        return self.id == other.id

    def add_quantity(self, amount: int) -> int:
        """
        Add quantity to this stack.

        Returns:
            Amount actually added (may be less if stack limit reached)
        """
        space_available = self.max_stack_size - self.quantity
        to_add = min(amount, space_available)
        self.quantity += to_add
        return to_add

    def remove_quantity(self, amount: int) -> int:
        """
        Remove quantity from this stack.

        Returns:
            Amount actually removed
        """
        to_remove = min(amount, self.quantity)
        self.quantity -= to_remove
        return to_remove

    def is_empty(self) -> bool:
        """Check if stack is empty."""
        return self.quantity <= 0

    def is_full(self) -> bool:
        """Check if stack is at maximum capacity."""
        return self.quantity >= self.max_stack_size

    def copy(self) -> ItemStack:
        """Create a copy of this stack."""
        return ItemStack(data=self.data.copy(), quantity=self.quantity)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for save/load."""
        return {
            "id": self.id,
            "quantity": self.quantity,
        }

    @classmethod
    def from_dict(cls, item_data: dict[str, Any], quantity: int = 1) -> ItemStack:
        """Deserialize from dictionary."""
        return cls(data=item_data, quantity=quantity)


@dataclass
class InventoryEvent:
    """
    Event object for inventory operations.

    Used by the event system to notify listeners of changes.
    """

    event_type: Literal[
        "item_added",
        "item_removed",
        "item_moved",
        "item_swapped",
        "stack_split",
        "inventory_cleared",
    ]
    inventory_id: str
    slot_index: int
    item_stack: Optional[ItemStack]
    previous_stack: Optional[ItemStack] = None
    source_inventory: Optional[str] = None
    source_slot: Optional[int] = None


RARITY_COLORS: dict[str, ColorLike] = {
    "common": (180, 180, 180, 255),
    "uncommon": (100, 200, 100, 255),
    "rare": (100, 150, 255, 255),
    "epic": (180, 100, 255, 255),
    "legendary": (255, 200, 50, 255),
}


DEFAULT_INVENTORY_CONFIG: InventoryConfig = {
    "rows": 4,
    "cols": 6,
    "slot_size": 48,
    "gap": 4,
    "allow_drag_drop": True,
    "allow_right_click_split": True,
    "allow_stack_swap": True,
    "max_weight": None,
    "auto_stack": True,
    "background_color": (40, 40, 45, 230),
    "slot_empty_color": (60, 60, 70, 200),
    "slot_filled_color": (80, 80, 90, 220),
    "slot_highlight_color": (100, 150, 200, 180),
    "slot_invalid_color": (200, 80, 80, 180),
    "border_color": (100, 100, 110, 255),
    "border_radius": 6,
    "border_width": 2,
    "tooltip_enabled": True,
    "tooltip_delay": 300,
}
