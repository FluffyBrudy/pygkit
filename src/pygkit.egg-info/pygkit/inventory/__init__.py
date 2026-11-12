"""
Pygkit Inventory System - Production-grade inventory management for Pygame.

A complete, generic, and optimized inventory system with:
- Data-driven item definitions
- Grid-based slot management
- Drag-and-drop interactions
- Tooltips and visual feedback
- Asset caching for performance
- Event-driven architecture
- Save/load serialization support

Modules:
    data: Type definitions and data structures
    core: Inventory logic and state management
    assets: Asset caching and procedural generation
    ui: UI rendering and user interaction

Usage:
    from pygkit.inventory import Inventory, InventoryWidget, ItemData
    
    # Create inventory
    config = {"rows": 4, "cols": 6, "slot_size": 48}
    inventory = Inventory("player_backpack", config)
    
    # Add items
    item: ItemData = {
        "id": "health_potion",
        "name": "Health Potion",
        "description": "Restores 50 HP",
        "stack_size": 99,
        "icon_color": (200, 50, 50, 255),
        "icon_shape": "circle",
        "value": 25,
        "weight": 0.5,
    }
    inventory.add_item(item, quantity=5)
    
    # Create UI widget
    widget = InventoryWidget(inventory, position=(100, 100))
    
    # In game loop:
    widget.handle_events(pygame.event.get())
    widget.update(dt)
    widget.render(screen)
"""

from .data import (
    ItemData,
    InventoryConfig,
    ItemStack,
    InventoryEvent,
    RARITY_COLORS,
    DEFAULT_INVENTORY_CONFIG,
)
from .core import Inventory
from .assets import (
    AssetCache,
    get_cache,
    generate_procedural_icon,
    render_quantity_text,
)
from .ui import (
    Tooltip,
    DragDropState,
    InventoryWidget,
    InventoryManager,
)

__all__ = [
    # Data structures
    "ItemData",
    "InventoryConfig",
    "ItemStack",
    "InventoryEvent",
    "RARITY_COLORS",
    "DEFAULT_INVENTORY_CONFIG",
    
    # Core logic
    "Inventory",
    
    # Assets
    "AssetCache",
    "get_cache",
    "generate_procedural_icon",
    "render_quantity_text",
    
    # UI components
    "Tooltip",
    "DragDropState",
    "InventoryWidget",
    "InventoryManager",
]
