"""
Gate registry for automatic gate discovery and registration
"""

from typing import Dict, List, Type

from .base_gate import BaseGate

# Global registry of gate classes
_gate_registry: Dict[str, Type[BaseGate]] = {}


def register_gate(cls: Type[BaseGate]) -> Type[BaseGate]:
    """
    Decorator to register a gate class in the global registry.

    Usage:
        @register_gate
        class MyGate(BaseGate):
            ...
    """
    _gate_registry[cls.__name__] = cls
    return cls


def get_registered_gates() -> List[Type[BaseGate]]:
    """Return all registered gate classes, sorted by their order property."""
    gate_classes = list(_gate_registry.values())
    gate_classes.sort(
        key=lambda cls: cls.__dict__.get('order', property()).fget(None)
        if 'order' in cls.__dict__ and callable(getattr(cls.__dict__['order'], 'fget', None))
        else 999
    )
    return gate_classes


def clear_registry():
    """Clear the gate registry (useful for testing)."""
    _gate_registry.clear()
