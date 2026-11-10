import unittest

from nbafantasy.common.logger import Logger
from nbafantasy.common.singleton import Singleton


class SingletonTest(unittest.TestCase):
    def test_same_instance(self):
        self.assertIs(Logger(), Logger())

    def test_reset_creates_a_new_instance(self):
        class Thing(metaclass=Singleton):
            def __init__(self, n=0):
                self.n = n

        first = Thing(1)
        self.assertIs(Thing(2), first)
        self.assertEqual(Thing().n, 1)
        Thing.reset()
        self.assertEqual(Thing(3).n, 3)


if __name__ == "__main__":
    unittest.main()
