"""
Core inventory logic and management.

Provides the Inventory class with item operations, event system,
and state management independent of UI rendering.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from .data import (
    DEFAULT_INVENTORY_CONFIG,
    InventoryConfig,
    InventoryEvent,
    ItemData,
    ItemStack,
)


class Inventory:
    """
    Generic inventory container with full item management capabilities.

    Features:
    - Grid-based slot system with configurable size
    - Automatic stacking for stackable items
    - Event system for external reactions to changes
    - Weight tracking for encumbrance systems
    - Tag-based item filtering
    - Serialization support for save/load

    Usage:
        config: InventoryConfig = {
            "rows": 4,
            "cols": 6,
            "slot_size": 48,
            "auto_stack": True,
        }

        inventory = Inventory("player_backpack", config)


        item_data: ItemData = {
            "id": "potion_health",
            "name": "Health Potion",
            "stack_size": 99,
            "icon_color": (200, 50, 50, 255),
            "icon_shape": "circle",
        }
        inventory.add_item(item_data, quantity=5)


        for event in inventory.get_events():
            print(f"Event: {event.event_type}")
    """

    def __init__(
        self,
        inventory_id: str,
        config: Optional[InventoryConfig] = None,
    ) -> None:
        """
        Initialize an inventory.

        Args:
            inventory_id: Unique identifier for this inventory
            config: Configuration options (uses defaults if not provided)
        """
        self.inventory_id = inventory_id
        self.config = {**DEFAULT_INVENTORY_CONFIG, **(config or {})}

        self.rows: int = self.config.get("rows", 4)
        self.cols: int = self.config.get("cols", 6)
        self.total_slots: int = self.rows * self.cols

        self._slots: List[Optional[ItemStack]] = [None] * self.total_slots

        self._events: List[InventoryEvent] = []

        self._listeners: List[Callable[[InventoryEvent], None]] = []

        self._total_weight: float = 0.0

    @property
    def total_weight(self) -> float:
        """Get current total weight of all items."""
        return self._total_weight

    @property
    def max_weight(self) -> Optional[float]:
        """Get maximum allowed weight (None = unlimited)."""
        return self.config.get("max_weight")

    @property
    def is_over_encumbered(self) -> bool:
        """Check if inventory exceeds weight limit."""
        max_w = self.max_weight
        return max_w is not None and self._total_weight > max_w

    def add_listener(self, callback: Callable[[InventoryEvent], None]) -> None:
        """Register an event listener."""
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[InventoryEvent], None]) -> None:
        """Remove an event listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _emit_event(self, event: InventoryEvent) -> None:
        """Emit an event to all listeners."""
        self._events.append(event)
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass

    def get_events(self) -> List[InventoryEvent]:
        """Get and clear the event queue."""
        events = self._events.copy()
        self._events.clear()
        return events

    def _update_weight(self) -> None:
        """Recalculate total weight from all slots."""
        self._total_weight = sum(stack.weight for stack in self._slots if stack is not None)

    def get_slot(self, index: int) -> Optional[ItemStack]:
        """Get the item stack at a specific slot."""
        if 0 <= index < self.total_slots:
            return self._slots[index]
        return None

    def set_slot(self, index: int, stack: Optional[ItemStack]) -> None:
        """
        Set the item stack at a specific slot.

        Warning: This bypasses validation. Use add_item/move_item instead.
        """
        if 0 <= index < self.total_slots:
            old_stack = self._slots[index]

            if old_stack:
                self._total_weight -= old_stack.weight
            if stack:
                self._total_weight += stack.weight

            self._slots[index] = stack

    def find_empty_slot(self) -> int:
        """Find the first empty slot, or -1 if none available."""
        for i, slot in enumerate(self._slots):
            if slot is None:
                return i
        return -1

    def find_item(self, item_id: str) -> List[int]:
        """Find all slots containing a specific item ID."""
        return [i for i, stack in enumerate(self._slots) if stack is not None and stack.id == item_id]

    def find_items_by_tag(self, tag: str) -> List[int]:
        """Find all slots containing items with a specific tag."""
        return [i for i, stack in enumerate(self._slots) if stack is not None and tag in stack.tags]

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if inventory has at least the specified quantity of an item."""
        total = 0
        for stack in self._slots:
            if stack and stack.id == item_id:
                total += stack.quantity
        return total >= quantity

    def count_item(self, item_id: str) -> int:
        """Count total quantity of a specific item across all slots."""
        total = 0
        for stack in self._slots:
            if stack and stack.id == item_id:
                total += stack.quantity
        return total

    def add_item(
        self,
        item_data: ItemData | dict[str, Any],
        quantity: int = 1,
    ) -> int:
        """
        Add an item to the inventory.

        If auto_stack is enabled, will stack with existing items first.

        Args:
            item_data: Item definition (dict with required 'id' and 'name')
            quantity: Amount to add

        Returns:
            Amount actually added (may be less if inventory is full)
        """
        if quantity <= 0:
            return 0

        data_dict = dict(item_data)

        max_stack = data_dict.get("stack_size", 1)
        if max_stack <= 0:
            max_stack = 1

        remaining = quantity
        auto_stack = self.config.get("auto_stack", True)

        if auto_stack and max_stack > 1:
            for i, stack in enumerate(self._slots):
                if stack and stack.data.get("id") == data_dict.get("id"):
                    space = stack.max_stack_size - stack.quantity
                    to_add = min(remaining, space)
                    if to_add > 0:
                        stack.add_quantity(to_add)
                        remaining -= to_add

                        self._emit_event(
                            InventoryEvent(
                                event_type="item_added",
                                inventory_id=self.inventory_id,
                                slot_index=i,
                                item_stack=stack,
                            )
                        )

                        if remaining <= 0:
                            self._update_weight()
                            return quantity

        while remaining > 0:
            slot_index = self.find_empty_slot()
            if slot_index == -1:
                break

            stack_quantity = min(remaining, max_stack)
            new_stack = ItemStack(data=data_dict, quantity=stack_quantity)
            self._slots[slot_index] = new_stack
            remaining -= stack_quantity

            self._emit_event(
                InventoryEvent(
                    event_type="item_added",
                    inventory_id=self.inventory_id,
                    slot_index=slot_index,
                    item_stack=new_stack,
                )
            )

        self._update_weight()
        return quantity - remaining

    def remove_item(
        self,
        item_id: str,
        quantity: int = 1,
    ) -> int:
        """
        Remove an item from the inventory.

        Removes from stacks starting from the first found.

        Args:
            item_id: ID of item to remove
            quantity: Amount to remove

        Returns:
            Amount actually removed
        """
        if quantity <= 0:
            return 0

        remaining = quantity

        for i, stack in enumerate(self._slots):
            if stack and stack.id == item_id:
                removed = stack.remove_quantity(remaining)
                remaining -= removed

                if stack.is_empty():
                    self._slots[i] = None

                self._emit_event(
                    InventoryEvent(
                        event_type="item_removed",
                        inventory_id=self.inventory_id,
                        slot_index=i,
                        item_stack=stack if not stack.is_empty() else None,
                        previous_stack=stack,
                    )
                )

                if remaining <= 0:
                    break

        self._update_weight()
        return quantity - remaining

    def remove_from_slot(
        self,
        slot_index: int,
        quantity: Optional[int] = None,
    ) -> Optional[ItemStack]:
        """
        Remove an item from a specific slot.

        Args:
            slot_index: Slot to remove from
            quantity: Amount to remove (None = entire stack)

        Returns:
            The removed stack (or partial stack), or None if slot was empty
        """
        if not 0 <= slot_index < self.total_slots:
            return None

        stack = self._slots[slot_index]
        if stack is None:
            return None

        previous_stack = stack.copy()

        if quantity is None or quantity >= stack.quantity:
            self._slots[slot_index] = None
            self._emit_event(
                InventoryEvent(
                    event_type="item_removed",
                    inventory_id=self.inventory_id,
                    slot_index=slot_index,
                    item_stack=None,
                    previous_stack=previous_stack,
                )
            )
        else:
            stack.remove_quantity(quantity)
            removed_stack = ItemStack(data=stack.data, quantity=quantity)
            self._emit_event(
                InventoryEvent(
                    event_type="item_removed",
                    inventory_id=self.inventory_id,
                    slot_index=slot_index,
                    item_stack=stack,
                    previous_stack=previous_stack,
                )
            )
            return removed_stack

        self._update_weight()
        return previous_stack

    def move_item(
        self,
        from_slot: int,
        to_slot: int,
        quantity: Optional[int] = None,
    ) -> bool:
        """
        Move an item between slots (within same inventory).

        Handles stacking automatically if target slot has compatible item.

        Args:
            from_slot: Source slot index
            to_slot: Destination slot index
            quantity: Amount to move (None = entire stack)

        Returns:
            True if move was successful, False otherwise
        """
        if not 0 <= from_slot < self.total_slots:
            return False
        if not 0 <= to_slot < self.total_slots:
            return False
        if from_slot == to_slot:
            return True

        source_stack = self._slots[from_slot]
        if source_stack is None:
            return False

        target_stack = self._slots[to_slot]

        if quantity is None:
            quantity = source_stack.quantity

        quantity = min(quantity, source_stack.quantity)
        if quantity <= 0:
            return False

        if target_stack and source_stack.can_stack_with(target_stack):
            space = target_stack.max_stack_size - target_stack.quantity
            to_move = min(quantity, space)

            if to_move > 0:
                target_stack.add_quantity(to_move)
                source_stack.remove_quantity(to_move)

                if source_stack.is_empty():
                    self._slots[from_slot] = None

                self._emit_event(
                    InventoryEvent(
                        event_type="item_moved",
                        inventory_id=self.inventory_id,
                        slot_index=to_slot,
                        item_stack=target_stack,
                        source_slot=from_slot,
                    )
                )

                self._update_weight()
                return source_stack.is_empty()

            return False

        if target_stack is None:
            if quantity >= source_stack.quantity:
                self._slots[to_slot] = source_stack
                self._slots[from_slot] = None
            else:
                moved_stack = ItemStack(
                    data=source_stack.data,
                    quantity=quantity,
                )
                source_stack.remove_quantity(quantity)
                self._slots[to_slot] = moved_stack

            self._emit_event(
                InventoryEvent(
                    event_type="item_moved",
                    inventory_id=self.inventory_id,
                    slot_index=to_slot,
                    item_stack=self._slots[to_slot],
                    source_slot=from_slot,
                )
            )

            self._update_weight()
            return True

        allow_swap = self.config.get("allow_stack_swap", True)
        if not allow_swap:
            return False

        self._slots[from_slot] = target_stack
        self._slots[to_slot] = source_stack

        self._emit_event(
            InventoryEvent(
                event_type="item_swapped",
                inventory_id=self.inventory_id,
                slot_index=to_slot,
                item_stack=source_stack,
                source_slot=from_slot,
            )
        )

        return True

    def split_stack(
        self,
        slot_index: int,
        quantity: int,
    ) -> Optional[ItemStack]:
        """
        Split a stack, moving part to an empty slot.

        Args:
            slot_index: Slot containing the stack to split
            quantity: Amount to move to new slot

        Returns:
            The new stack created, or None if split failed
        """
        if not 0 <= slot_index < self.total_slots:
            return None

        source_stack = self._slots[slot_index]
        if source_stack is None or not source_stack.is_stackable():
            return None

        if quantity <= 0 or quantity >= source_stack.quantity:
            return None

        empty_slot = self.find_empty_slot()
        if empty_slot == -1:
            return None

        new_stack = ItemStack(
            data=source_stack.data,
            quantity=quantity,
        )
        source_stack.remove_quantity(quantity)
        self._slots[empty_slot] = new_stack

        self._emit_event(
            InventoryEvent(
                event_type="stack_split",
                inventory_id=self.inventory_id,
                slot_index=empty_slot,
                item_stack=new_stack,
                source_slot=slot_index,
            )
        )

        return new_stack

    def clear(self) -> None:
        """Remove all items from the inventory."""
        for i, stack in enumerate(self._slots):
            if stack is not None:
                self._emit_event(
                    InventoryEvent(
                        event_type="item_removed",
                        inventory_id=self.inventory_id,
                        slot_index=i,
                        item_stack=None,
                        previous_stack=stack,
                    )
                )

        self._slots = [None] * self.total_slots
        self._total_weight = 0.0

        self._emit_event(
            InventoryEvent(
                event_type="inventory_cleared",
                inventory_id=self.inventory_id,
                slot_index=-1,
                item_stack=None,
            )
        )

    def is_full(self) -> bool:
        """Check if inventory has no empty slots."""
        return self.find_empty_slot() == -1

    def is_empty(self) -> bool:
        """Check if inventory has no items."""
        return all(stack is None for stack in self._slots)

    def get_contents(self) -> List[Tuple[int, ItemStack]]:
        """Get list of (slot_index, stack) tuples for non-empty slots."""
        return [(i, stack) for i, stack in enumerate(self._slots) if stack is not None]

    def to_dict(self) -> dict[str, Any]:
        """Serialize inventory to dictionary for save/load."""
        slots_data = []
        for i, stack in enumerate(self._slots):
            if stack is not None:
                slots_data.append(
                    {
                        "slot": i,
                        "item": stack.to_dict(),
                    }
                )

        return {
            "id": self.inventory_id,
            "config": dict(self.config),
            "slots": slots_data,
            "total_weight": self._total_weight,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        item_registry: dict[str, dict[str, Any]],
    ) -> Inventory:
        """
        Deserialize inventory from dictionary.

        Args:
            data: Serialized inventory data
            item_registry: Dictionary mapping item IDs to item definitions

        Returns:
            Reconstructed Inventory instance
        """
        config = data.get("config", {})
        inventory = cls(data.get("id", "unknown"), config)

        for slot_data in data.get("slots", []):
            slot_index = slot_data.get("slot", 0)
            item_data = slot_data.get("item", {})
            item_id = item_data.get("id", "")
            quantity = item_data.get("quantity", 1)

            if item_id in item_registry:
                full_item_data = item_registry[item_id]
                stack = ItemStack(data=full_item_data, quantity=quantity)
                if 0 <= slot_index < inventory.total_slots:
                    inventory._slots[slot_index] = stack

        inventory._update_weight()
        return inventory
