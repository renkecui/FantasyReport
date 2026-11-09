import unittest

from nbafantasy.stats.ranking import Ranking


class RankingTest(unittest.TestCase):
    def test_higher_is_better_with_ties(self):
        self.assertEqual(Ranking.competition([10, 30, 30, 5]), [3, 1, 1, 4])

    def test_lower_is_better(self):
        self.assertEqual(Ranking.competition([60, 45, 60, 70], lower_is_better=True), [2, 1, 2, 4])

    def test_empty(self):
        self.assertEqual(Ranking.competition([]), [])


if __name__ == "__main__":
    unittest.main()
