"""
Unit tests for the Inventory System.

Tests the purely logical aspects: item management, stacking, events,
weight tracking, and serialization without UI dependencies.
"""

import pytest

from pygkit.inventory.core import Inventory
from pygkit.inventory.data import (
    DEFAULT_INVENTORY_CONFIG,
    RARITY_COLORS,
    InventoryConfig,
    InventoryEvent,
    ItemData,
    ItemStack,
)


class TestItemStack:
    """Test ItemStack data structure and operations."""

    def test_item_stack_creation(self):
        """Test creating an item stack."""
        item_data: ItemData = {
            "id": "potion_health",
            "name": "Health Potion",
            "stack_size": 99,
        }
        stack = ItemStack(data=item_data, quantity=5)

        assert stack.id == "potion_health"
        assert stack.name == "Health Potion"
        assert stack.quantity == 5
        assert stack.max_stack_size == 99

    def test_item_stack_defaults(self):
        """Test default values for item stack."""
        item_data: ItemData = {"id": "sword", "name": "Iron Sword"}
        stack = ItemStack(data=item_data)

        assert stack.quantity == 1
        assert stack.max_stack_size == 1  # Default when not specified

    def test_item_stack_properties(self):
        """Test item stack computed properties."""
        item_data: ItemData = {
            "id": "coin",
            "name": "Gold Coin",
            "weight": 0.1,
            "value": 1,
            "stack_size": 999,
            "tags": ["currency", "valuable"],
            "rarity": "common",
        }
        stack = ItemStack(data=item_data, quantity=10)

        assert stack.weight == 1.0  # 0.1 * 10
        assert stack.value == 10  # 1 * 10
        assert "currency" in stack.tags
        assert stack.rarity == "common"

    def test_is_stackable(self):
        """Test stackable detection."""
        stackable_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}
        unstackable_data: ItemData = {
            "id": "sword",
            "name": "Sword",
            "stack_size": 1,
        }

        stackable = ItemStack(data=stackable_data)
        unstackable = ItemStack(data=unstackable_data)

        assert stackable.is_stackable() is True
        assert unstackable.is_stackable() is False

    def test_can_stack_with(self):
        """Test stack compatibility checking."""
        data1: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        data2: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        data3: ItemData = {"id": "elixir", "name": "Elixir", "stack_size": 10}
        data4: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        stack1 = ItemStack(data=data1)
        stack2 = ItemStack(data=data2)
        stack3 = ItemStack(data=data3)
        stack4 = ItemStack(data=data4)

        assert stack1.can_stack_with(stack2) is True
        assert stack1.can_stack_with(stack3) is False
        assert stack1.can_stack_with(stack4) is False

    def test_add_quantity(self):
        """Test adding quantity to stack."""
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}
        stack = ItemStack(data=item_data, quantity=10)

        added = stack.add_quantity(20)

        assert added == 20
        assert stack.quantity == 30

    def test_add_quantity_exceeds_max(self):
        """Test adding quantity that exceeds max stack size."""
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}
        stack = ItemStack(data=item_data, quantity=60)

        added = stack.add_quantity(10)

        assert added == 4  # Only 4 can fit
        assert stack.quantity == 64

    def test_remove_quantity(self):
        """Test removing quantity from stack."""
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        stack = ItemStack(data=item_data, quantity=10)

        removed = stack.remove_quantity(3)

        assert removed == 3
        assert stack.quantity == 7

    def test_remove_quantity_exceeds_available(self):
        """Test removing more than available quantity."""
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        stack = ItemStack(data=item_data, quantity=5)

        removed = stack.remove_quantity(10)

        assert removed == 5  # Only 5 available
        assert stack.quantity == 0

    def test_is_empty(self):
        """Test empty stack detection."""
        item_data: ItemData = {"id": "item", "name": "Item", "stack_size": 10}
        stack = ItemStack(data=item_data, quantity=1)

        assert stack.is_empty() is False

        stack.remove_quantity(1)
        assert stack.is_empty() is True

    def test_is_full(self):
        """Test full stack detection."""
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}
        stack = ItemStack(data=item_data, quantity=64)

        assert stack.is_full() is True

        stack.remove_quantity(1)
        assert stack.is_full() is False

    def test_copy(self):
        """Test copying a stack."""
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        stack1 = ItemStack(data=item_data, quantity=5)

        stack2 = stack1.copy()

        assert stack2.id == stack1.id
        assert stack2.quantity == stack1.quantity
        assert stack2 is not stack1  # Different objects

    def test_to_dict(self):
        """Test serialization to dictionary."""
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        stack = ItemStack(data=item_data, quantity=5)

        data = stack.to_dict()

        assert data["id"] == "potion"
        assert data["quantity"] == 5

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        item_data: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}
        stack = ItemStack.from_dict(item_data, quantity=1)

        assert stack.id == "sword"
        assert stack.quantity == 1


class TestInventory:
    """Test Inventory core logic and operations."""

    def test_inventory_creation(self):
        """Test creating an inventory."""
        inventory = Inventory("player_backpack")

        assert inventory.inventory_id == "player_backpack"
        assert inventory.rows == 4
        assert inventory.cols == 6
        assert inventory.total_slots == 24
        assert inventory.is_empty() is True

    def test_inventory_with_custom_config(self):
        """Test creating inventory with custom config."""
        config: InventoryConfig = {"rows": 5, "cols": 8}
        inventory = Inventory("chest", config)

        assert inventory.rows == 5
        assert inventory.cols == 8
        assert inventory.total_slots == 40

    def test_add_item(self):
        """Test adding an item to inventory."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "potion", "name": "Health Potion", "stack_size": 10}

        added = inventory.add_item(item_data, quantity=5)

        assert added == 5
        assert inventory.count_item("potion") == 5
        assert inventory.is_empty() is False

    def test_add_multiple_items(self):
        """Test adding multiple different items."""
        inventory = Inventory("player")
        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        sword: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory.add_item(potion, quantity=3)
        inventory.add_item(sword, quantity=1)

        assert inventory.count_item("potion") == 3
        assert inventory.count_item("sword") == 1

    def test_auto_stacking(self):
        """Test automatic stacking of identical items."""
        config: InventoryConfig = {"auto_stack": True}
        inventory = Inventory("player", config)
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}

        inventory.add_item(item_data, quantity=30)
        inventory.add_item(item_data, quantity=20)

        assert inventory.count_item("arrow") == 50
        # Should be in one slot
        slots = inventory.find_item("arrow")
        assert len(slots) == 1

    def test_stacking_overflow(self):
        """Test stacking that exceeds max stack size."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}

        inventory.add_item(item_data, quantity=70)

        assert inventory.count_item("arrow") == 70
        slots = inventory.find_item("arrow")
        assert len(slots) == 2  # Should occupy 2 slots

    def test_add_to_full_inventory(self):
        """Test adding items when inventory is full."""
        config: InventoryConfig = {"rows": 1, "cols": 2}
        inventory = Inventory("small", config)

        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 1}

        inventory.add_item(potion, quantity=1)
        inventory.add_item(potion, quantity=1)
        # Inventory is now full

        added = inventory.add_item(potion, quantity=1)

        assert added == 0  # Nothing added
        assert inventory.count_item("potion") == 2

    def test_remove_item(self):
        """Test removing an item from inventory."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item_data, quantity=10)
        removed = inventory.remove_item("potion", quantity=3)

        assert removed == 3
        assert inventory.count_item("potion") == 7

    def test_remove_more_than_available(self):
        """Test removing more items than available."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item_data, quantity=5)
        removed = inventory.remove_item("potion", quantity=10)

        assert removed == 5  # Only 5 available
        assert inventory.count_item("potion") == 0

    def test_remove_from_multiple_stacks(self):
        """Test removal from multiple stacks."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}

        inventory.add_item(item_data, quantity=70)  # Creates 2 stacks
        removed = inventory.remove_item("arrow", quantity=70)

        assert removed == 70
        assert inventory.count_item("arrow") == 0

    def test_remove_from_slot(self):
        """Test removing from specific slot."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item_data, quantity=5)
        slots = inventory.find_item("potion")
        slot_index = slots[0]

        removed = inventory.remove_from_slot(slot_index, quantity=3)

        assert removed is not None
        assert removed.quantity == 3
        assert inventory.count_item("potion") == 2

    def test_remove_entire_slot(self):
        """Test removing entire slot."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory.add_item(item_data, quantity=1)
        slots = inventory.find_item("sword")
        slot_index = slots[0]

        removed = inventory.remove_from_slot(slot_index)

        assert removed is not None
        assert removed.id == "sword"
        assert inventory.get_slot(slot_index) is None

    def test_move_item(self):
        """Test moving item between slots."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item_data, quantity=5)
        from_slot = inventory.find_item("potion")[0]
        to_slot = inventory.find_empty_slot()

        success = inventory.move_item(from_slot, to_slot)

        assert success is True
        assert inventory.get_slot(from_slot) is None
        assert inventory.get_slot(to_slot) is not None

    def test_move_item_with_stacking(self):
        """Test moving item to slot with same item (auto-stack)."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}

        inventory.set_slot(0, ItemStack(data=item_data, quantity=30))
        inventory.set_slot(1, ItemStack(data=item_data, quantity=20))

        success = inventory.move_item(0, 1)

        assert success is True
        stack = inventory.get_slot(1)
        assert stack is not None
        assert stack.quantity == 50

    def test_move_item_swap(self):
        """Test swapping items between slots."""
        config: InventoryConfig = {"allow_stack_swap": True}
        inventory = Inventory("player", config)

        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 1}
        sword: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory.set_slot(0, ItemStack(data=potion))
        inventory.set_slot(1, ItemStack(data=sword))

        success = inventory.move_item(0, 1)

        assert success is True
        assert inventory.get_slot(0).id == "sword"
        assert inventory.get_slot(1).id == "potion"

    def test_split_stack(self):
        """Test splitting a stack."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "arrow", "name": "Arrow", "stack_size": 64}

        inventory.add_item(item_data, quantity=20)
        slot_index = inventory.find_item("arrow")[0]

        new_stack = inventory.split_stack(slot_index, quantity=10)

        assert new_stack is not None
        assert new_stack.quantity == 10
        assert inventory.get_slot(slot_index).quantity == 10

    def test_split_unstackable_fails(self):
        """Test that splitting unstackable items fails."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory.add_item(item_data, quantity=1)
        slot_index = inventory.find_item("sword")[0]

        new_stack = inventory.split_stack(slot_index, quantity=1)

        assert new_stack is None

    def test_find_item(self):
        """Test finding items by ID."""
        inventory = Inventory("player")
        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(potion, quantity=5)
        inventory.add_item(potion, quantity=3)

        slots = inventory.find_item("potion")

        assert len(slots) >= 1
        assert all(inventory.get_slot(s).id == "potion" for s in slots)

    def test_find_items_by_tag(self):
        """Test finding items by tag."""
        inventory = Inventory("player")
        potion: ItemData = {
            "id": "potion",
            "name": "Potion",
            "tags": ["consumable", "healing"],
            "stack_size": 10,
        }
        sword: ItemData = {"id": "sword", "name": "Sword", "tags": ["weapon"], "stack_size": 1}

        inventory.add_item(potion, quantity=1)
        inventory.add_item(sword, quantity=1)

        consumables = inventory.find_items_by_tag("consumable")
        weapons = inventory.find_items_by_tag("weapon")

        assert len(consumables) == 1
        assert len(weapons) == 1

    def test_has_item(self):
        """Test checking if inventory has item."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "key", "name": "Key", "stack_size": 1}

        assert inventory.has_item("key") is False

        inventory.add_item(item_data, quantity=1)

        assert inventory.has_item("key") is True
        assert inventory.has_item("key", quantity=2) is False

    def test_count_item(self):
        """Test counting item quantity."""
        inventory = Inventory("player")
        item_data: ItemData = {"id": "coin", "name": "Coin", "stack_size": 999}

        inventory.add_item(item_data, quantity=150)

        assert inventory.count_item("coin") == 150
        assert inventory.count_item("unknown") == 0

    def test_clear(self):
        """Test clearing inventory."""
        inventory = Inventory("player")
        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(potion, quantity=10)
        inventory.clear()

        assert inventory.is_empty() is True
        assert inventory.count_item("potion") == 0

    def test_is_full(self):
        """Test checking if inventory is full."""
        config: InventoryConfig = {"rows": 1, "cols": 2}
        inventory = Inventory("small", config)

        assert inventory.is_full() is False

        item: ItemData = {"id": "item", "name": "Item", "stack_size": 1}
        inventory.add_item(item, quantity=1)
        inventory.add_item(item, quantity=1)

        assert inventory.is_full() is True

    def test_is_empty(self):
        """Test checking if inventory is empty."""
        inventory = Inventory("player")

        assert inventory.is_empty() is True

        item: ItemData = {"id": "item", "name": "Item", "stack_size": 1}
        inventory.add_item(item, quantity=1)

        assert inventory.is_empty() is False

    def test_get_contents(self):
        """Test getting inventory contents."""
        inventory = Inventory("player")
        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        sword: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory.add_item(potion, quantity=5)
        inventory.add_item(sword, quantity=1)

        contents = inventory.get_contents()

        assert len(contents) == 2
        assert all(isinstance(slot_idx, int) and isinstance(stack, ItemStack) for slot_idx, stack in contents)


class TestInventoryWeight:
    """Test weight tracking system."""

    def test_weight_tracking(self):
        """Test that weight is tracked correctly."""
        inventory = Inventory("player")
        item: ItemData = {"id": "rock", "name": "Rock", "weight": 5.0, "stack_size": 10}

        inventory.add_item(item, quantity=3)

        assert inventory.total_weight == 15.0

    def test_weight_after_removal(self):
        """Test weight updates after removal."""
        inventory = Inventory("player")
        item: ItemData = {"id": "rock", "name": "Rock", "weight": 5.0, "stack_size": 10}

        inventory.add_item(item, quantity=5)
        inventory.remove_item("rock", quantity=2)

        assert inventory.total_weight == 15.0

    def test_max_weight(self):
        """Test max weight configuration."""
        config: InventoryConfig = {"max_weight": 50.0}
        inventory = Inventory("player", config)

        assert inventory.max_weight == 50.0

    def test_over_encumbered(self):
        """Test over-encumbered detection."""
        config: InventoryConfig = {"max_weight": 20.0}
        inventory = Inventory("player", config)
        item: ItemData = {"id": "rock", "name": "Rock", "weight": 10.0, "stack_size": 10}

        inventory.add_item(item, quantity=2)
        assert inventory.is_over_encumbered is False

        inventory.add_item(item, quantity=1)
        assert inventory.is_over_encumbered is True


class TestInventoryEvents:
    """Test event system."""

    def test_event_on_add(self):
        """Test event is emitted when item is added."""
        inventory = Inventory("player")
        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item, quantity=1)
        events = inventory.get_events()

        assert len(events) == 1
        assert events[0].event_type == "item_added"

    def test_event_on_remove(self):
        """Test event is emitted when item is removed."""
        inventory = Inventory("player")
        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item, quantity=5)
        inventory.get_events()  # Clear add events

        inventory.remove_item("potion", quantity=2)
        events = inventory.get_events()

        assert len(events) == 1
        assert events[0].event_type == "item_removed"

    def test_event_on_move(self):
        """Test event is emitted when item is moved."""
        inventory = Inventory("player")
        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item, quantity=1)
        from_slot = inventory.find_item("potion")[0]
        to_slot = inventory.find_empty_slot()
        inventory.get_events()  # Clear add events

        inventory.move_item(from_slot, to_slot)
        events = inventory.get_events()

        assert len(events) == 1
        assert events[0].event_type == "item_moved"

    def test_event_on_clear(self):
        """Test event is emitted when inventory is cleared."""
        inventory = Inventory("player")
        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item, quantity=5)
        inventory.get_events()  # Clear add events

        inventory.clear()
        events = inventory.get_events()

        # Should have item_removed events + inventory_cleared
        assert any(e.event_type == "inventory_cleared" for e in events)

    def test_event_listener(self):
        """Test event listener callback."""
        inventory = Inventory("player")
        received_events = []

        def listener(event: InventoryEvent):
            received_events.append(event)

        inventory.add_listener(listener)

        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        inventory.add_item(item, quantity=1)

        assert len(received_events) == 1
        assert received_events[0].event_type == "item_added"

    def test_remove_listener(self):
        """Test removing event listener."""
        inventory = Inventory("player")
        received_events = []

        def listener(event: InventoryEvent):
            received_events.append(event)

        inventory.add_listener(listener)
        inventory.remove_listener(listener)

        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        inventory.add_item(item, quantity=1)

        assert len(received_events) == 0


class TestInventorySerialization:
    """Test serialization and deserialization."""

    def test_to_dict(self):
        """Test serializing inventory to dictionary."""
        inventory = Inventory("player")
        item: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}

        inventory.add_item(item, quantity=5)

        data = inventory.to_dict()

        assert data["id"] == "player"
        assert "slots" in data
        assert len(data["slots"]) == 1

    def test_from_dict(self):
        """Test deserializing inventory from dictionary."""
        item_registry = {
            "potion": {"id": "potion", "name": "Health Potion", "stack_size": 10},
        }

        data = {
            "id": "player",
            "config": {"rows": 4, "cols": 6},
            "slots": [{"slot": 0, "item": {"id": "potion", "quantity": 5}}],
        }

        inventory = Inventory.from_dict(data, item_registry)

        assert inventory.inventory_id == "player"
        assert inventory.count_item("potion") == 5

    def test_roundtrip_serialization(self):
        """Test complete serialization roundtrip."""
        inventory1 = Inventory("test")
        potion: ItemData = {"id": "potion", "name": "Potion", "stack_size": 10}
        sword: ItemData = {"id": "sword", "name": "Sword", "stack_size": 1}

        inventory1.add_item(potion, quantity=7)
        inventory1.add_item(sword, quantity=1)

        # Serialize
        data = inventory1.to_dict()

        # Deserialize
        item_registry = {
            "potion": {"id": "potion", "name": "Potion", "stack_size": 10},
            "sword": {"id": "sword", "name": "Sword", "stack_size": 1},
        }
        inventory2 = Inventory.from_dict(data, item_registry)

        assert inventory2.count_item("potion") == 7
        assert inventory2.count_item("sword") == 1


class TestRarityColors:
    """Test rarity color constants."""

    def test_rarity_colors_exist(self):
        """Test that all rarity colors are defined."""
        assert "common" in RARITY_COLORS
        assert "uncommon" in RARITY_COLORS
        assert "rare" in RARITY_COLORS
        assert "epic" in RARITY_COLORS
        assert "legendary" in RARITY_COLORS

    def test_rarity_colors_format(self):
        """Test that rarity colors are properly formatted."""
        for color in RARITY_COLORS.values():
            assert isinstance(color, tuple)
            assert len(color) == 4  # RGBA


class TestDefaultConfig:
    """Test default configuration constants."""

    def test_default_config_exists(self):
        """Test that default config is defined."""
        assert DEFAULT_INVENTORY_CONFIG is not None

    def test_default_config_values(self):
        """Test default config has expected values."""
        assert DEFAULT_INVENTORY_CONFIG["rows"] == 4
        assert DEFAULT_INVENTORY_CONFIG["cols"] == 6
        assert DEFAULT_INVENTORY_CONFIG["auto_stack"] is True
