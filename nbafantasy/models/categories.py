class Categories:
    """The league's scoring categories and the per-game stats shown for players."""

    # The 9 head-to-head categories, in sheet order.
    ALL = ("FG%", "FT%", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS")
    # Per-game averages shown for each player.
    PLAYER_STATS = ("MIN", "FGM", "FGA", "FTM", "FTA", "3PM", "REB", "AST", "STL", "BLK", "TO", "PTS")
    LOWER_IS_BETTER = frozenset({"TO"})
    PERCENT = frozenset({"FG%", "FT%"})

    @classmethod
    def lower_is_better(cls, cat):
        return cat in cls.LOWER_IS_BETTER

    @classmethod
    def is_percent(cls, cat):
        return cat in cls.PERCENT
