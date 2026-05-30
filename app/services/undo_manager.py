"""Simple undo stack for reversible operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class UndoAction:
    """A single undoable action."""

    action_type: str
    description: str
    undo_fn: Callable[[], None]


class UndoManager:
    """Simple undo stack with a maximum depth."""

    _MAX_STACK = 20

    def __init__(self) -> None:
        self._stack: list[UndoAction] = []

    def push_action(
        self, action_type: str, undo_fn: Callable[[], None], description: str
    ) -> None:
        """Add an action to the undo stack, trimming to max size."""
        self._stack.append(
            UndoAction(action_type=action_type, description=description, undo_fn=undo_fn)
        )
        if len(self._stack) > self._MAX_STACK:
            self._stack = self._stack[-self._MAX_STACK :]

    def undo(self) -> str | None:
        """Pop and execute the last action. Returns description or None if empty."""
        if not self._stack:
            return None
        action = self._stack.pop()
        action.undo_fn()
        return action.description

    def can_undo(self) -> bool:
        """Return True if there are actions to undo."""
        return len(self._stack) > 0

    def peek_description(self) -> str | None:
        """Return description of the top action without executing it."""
        if not self._stack:
            return None
        return self._stack[-1].description


# Global singleton instance
undo_manager = UndoManager()
