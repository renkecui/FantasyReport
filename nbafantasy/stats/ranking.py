from typing import List, Sequence


class Ranking:
    """How the league ranks teams."""

    @staticmethod
    def competition(values: Sequence[float], lower_is_better=False) -> List[int]:
        """Rank each value: 1 + how many values are strictly better. Ties share the best rank
        ("1, 2, 2, 4"), like the workbook's COUNTIFS(...)+1 and RANK formulas."""
        if lower_is_better:
            return [1 + sum(1 for o in values if o < v) for v in values]
        return [1 + sum(1 for o in values if o > v) for v in values]
