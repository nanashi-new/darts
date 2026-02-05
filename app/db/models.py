class Player:
    """Placeholder data model for players."""

    def __init__(self) -> None:
        self.id: int | None = None
        self.name: str = ""


class Tournament:
    """Placeholder data model for tournaments."""

    def __init__(self) -> None:
        self.id: int | None = None
        self.title: str = ""
