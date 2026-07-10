"""
Inventory System Demo for Pygkit.

Demonstrates the complete inventory system with:
- Multiple inventories (player backpack, chest)
- Drag and drop interactions
- Right-click stack splitting
- Tooltips with item information
- Event handling
- Various item types and rarities

Controls:
    I - Toggle player inventory
    C - Toggle chest inventory
    ESC - Close all inventories
    Mouse - Drag/drop items, right-click to split stacks
    Q - Quit demo
"""

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pygkit.inventory import (
    Inventory,
    InventoryManager,
    InventoryWidget,
    ItemData,
)


def create_sample_items() -> dict[str, ItemData]:
    """Create a registry of sample items for the demo."""
    return {
        "health_potion_small": {
            "id": "health_potion_small",
            "name": "Small Health Potion",
            "description": "Restores 25 HP. A common healing item.",
            "stack_size": 99,
            "icon_color": (220, 60, 60, 255),
            "icon_shape": "circle",
            "rarity": "common",
            "value": 10,
            "weight": 0.3,
            "tags": ["consumable", "healing"],
        },
        "health_potion_large": {
            "id": "health_potion_large",
            "name": "Large Health Potion",
            "description": "Restores 100 HP. Powerful healing brew.",
            "stack_size": 50,
            "icon_color": (180, 30, 30, 255),
            "icon_shape": "circle",
            "rarity": "uncommon",
            "value": 50,
            "weight": 0.5,
            "tags": ["consumable", "healing"],
        },
        "mana_potion": {
            "id": "mana_potion",
            "name": "Mana Potion",
            "description": "Restores 50 MP. Glows with arcane energy.",
            "stack_size": 99,
            "icon_color": (60, 100, 220, 255),
            "icon_shape": "diamond",
            "rarity": "common",
            "value": 15,
            "weight": 0.3,
            "tags": ["consumable", "mana"],
        },
        "iron_sword": {
            "id": "iron_sword",
            "name": "Iron Sword",
            "description": "A sturdy blade forged from quality iron.",
            "stack_size": 1,
            "icon_color": (180, 180, 200, 255),
            "icon_shape": "cross",
            "rarity": "common",
            "value": 75,
            "weight": 3.5,
            "tags": ["weapon", "melee"],
        },
        "steel_sword": {
            "id": "steel_sword",
            "name": "Steel Sword",
            "description": "A finely crafted blade of tempered steel.",
            "stack_size": 1,
            "icon_color": (200, 200, 230, 255),
            "icon_shape": "cross",
            "rarity": "uncommon",
            "value": 200,
            "weight": 3.0,
            "tags": ["weapon", "melee"],
        },
        "magic_staff": {
            "id": "magic_staff",
            "name": "Archmage's Staff",
            "description": "Crackles with raw magical power. Used by ancient wizards.",
            "stack_size": 1,
            "icon_color": (180, 100, 255, 255),
            "icon_shape": "star",
            "rarity": "epic",
            "value": 1500,
            "weight": 4.0,
            "tags": ["weapon", "magic", "staff"],
        },
        "gold_ring": {
            "id": "gold_ring",
            "name": "Gold Ring",
            "description": "A simple but valuable gold band.",
            "stack_size": 10,
            "icon_color": (255, 220, 50, 255),
            "icon_shape": "circle",
            "rarity": "uncommon",
            "value": 100,
            "weight": 0.1,
            "tags": ["accessory", "valuable"],
        },
        "dragon_amulet": {
            "id": "dragon_amulet",
            "name": "Dragon Amulet",
            "description": "Legendary amulet said to contain a dragon's essence.",
            "stack_size": 1,
            "icon_color": (255, 150, 50, 255),
            "icon_shape": "diamond",
            "rarity": "legendary",
            "value": 10000,
            "weight": 0.5,
            "tags": ["accessory", "legendary", "magic"],
        },
        "herb": {
            "id": "herb",
            "name": "Healing Herb",
            "description": "Common herb with mild healing properties.",
            "stack_size": 99,
            "icon_color": (80, 180, 80, 255),
            "icon_shape": "square",
            "rarity": "common",
            "value": 2,
            "weight": 0.1,
            "tags": ["material", "healing"],
        },
        "gem_ruby": {
            "id": "gem_ruby",
            "name": "Ruby",
            "description": "A flawless red gemstone of great value.",
            "stack_size": 50,
            "icon_color": (220, 40, 40, 255),
            "icon_shape": "diamond",
            "rarity": "rare",
            "value": 500,
            "weight": 0.2,
            "tags": ["material", "gem", "valuable"],
        },
        "shield_wood": {
            "id": "shield_wood",
            "name": "Wooden Shield",
            "description": "Basic protection made from reinforced oak.",
            "stack_size": 1,
            "icon_color": (139, 90, 43, 255),
            "icon_shape": "square",
            "rarity": "common",
            "value": 25,
            "weight": 2.0,
            "tags": ["armor", "shield"],
        },
        "key_bronze": {
            "id": "key_bronze",
            "name": "Bronze Key",
            "description": "An ornate key that opens something important.",
            "stack_size": 1,
            "icon_color": (205, 127, 50, 255),
            "icon_shape": "cross",
            "rarity": "uncommon",
            "value": 50,
            "weight": 0.1,
            "tags": ["key", "quest"],
        },
    }


def main():
    """Run the inventory demo."""

    pygame.init()

    screen_width = 1024
    screen_height = 768
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Pygkit Inventory System Demo")

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)

    item_registry = create_sample_items()

    player_config = {
        "rows": 5,
        "cols": 8,
        "slot_size": 50,
        "gap": 6,
        "auto_stack": True,
        "allow_drag_drop": True,
        "allow_right_click_split": True,
        "tooltip_enabled": True,
    }
    player_inventory = Inventory("player_backpack", player_config)

    player_inventory.add_item(item_registry["health_potion_small"], quantity=5)
    player_inventory.add_item(item_registry["mana_potion"], quantity=3)
    player_inventory.add_item(item_registry["herb"], quantity=15)
    player_inventory.add_item(item_registry["iron_sword"], quantity=1)
    player_inventory.add_item(item_registry["gold_ring"], quantity=2)
    player_inventory.add_item(item_registry["gem_ruby"], quantity=5)

    chest_config = {
        "rows": 4,
        "cols": 6,
        "slot_size": 50,
        "gap": 6,
        "auto_stack": True,
    }
    chest_inventory = Inventory("treasure_chest", chest_config)

    chest_inventory.add_item(item_registry["steel_sword"], quantity=1)
    chest_inventory.add_item(item_registry["magic_staff"], quantity=1)
    chest_inventory.add_item(item_registry["dragon_amulet"], quantity=1)
    chest_inventory.add_item(item_registry["health_potion_large"], quantity=10)
    chest_inventory.add_item(item_registry["key_bronze"], quantity=1)
    chest_inventory.add_item(item_registry["shield_wood"], quantity=1)

    player_widget = InventoryWidget(
        player_inventory,
        position=(50, 50),
        config=player_config,
    )

    chest_widget = InventoryWidget(
        chest_inventory,
        position=(50, 400),
        config=chest_config,
    )

    inv_manager = InventoryManager()
    inv_manager.register_inventory(player_inventory, player_widget)
    inv_manager.register_inventory(chest_inventory, chest_widget)

    inv_manager.open_inventory("player_backpack")

    running = True
    show_help = True

    while running:
        dt = clock.tick(60) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    inv_manager.close_all()

                elif event.key == pygame.K_i:
                    inv_manager.toggle_inventory("player_backpack")

                elif event.key == pygame.K_c:
                    inv_manager.toggle_inventory("treasure_chest")

                elif event.key == pygame.K_h:
                    show_help = not show_help

                elif event.key == pygame.K_q:
                    running = False

        inv_manager.handle_events(events)
        inv_manager.update(dt)

        screen.fill((30, 30, 35))

        if show_help:
            help_lines = [
                "Pygkit Inventory Demo",
                "",
                "Controls:",
                "  I - Toggle Player Inventory",
                "  C - Toggle Chest Inventory",
                "  ESC - Close All Inventories",
                "  H - Toggle This Help",
                "  Q - Quit",
                "",
                "Mouse:",
                "  Left Click + Drag - Move Items",
                "  Right Click + Drag - Split Stack",
            ]

            y_offset = 20
            for line in help_lines:
                text_surf = font.render(line, True, (200, 200, 200, 255))
                screen.blit(text_surf, (screen_width - 280, y_offset))
                y_offset += 22

        status_lines = [
            f"Player Weight: {player_inventory.total_weight:.1f}",
            f"Player Slots: {len(player_inventory.get_contents())}/{player_inventory.total_slots}",
            f"Chest Weight: {chest_inventory.total_weight:.1f}",
            f"Chest Slots: {len(chest_inventory.get_contents())}/{chest_inventory.total_slots}",
        ]

        y_offset = screen_height - 100
        for line in status_lines:
            text_surf = font.render(line, True, (150, 150, 150, 255))
            screen.blit(text_surf, (20, y_offset))
            y_offset += 22

        inv_manager.render(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
