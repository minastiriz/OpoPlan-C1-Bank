import unittest

from scripts.build_historical_packs import TOPIC_MAP_7_22, TOPIC_MAP_64_25, classify


class HistoricalTopicMappingTests(unittest.TestCase):
    def test_7_22_map_covers_every_question_exactly_once(self):
        self.assertEqual(set(TOPIC_MAP_7_22), set(range(1, 91)))

    def test_64_25_map_covers_every_question_exactly_once(self):
        self.assertEqual(set(TOPIC_MAP_64_25), set(range(1, 111)))

    def test_examples_found_during_physical_device_review(self):
        expected = {
            24: ("Parte especial", 7),
            47: ("Parte especial", 13),
            48: ("Parte especial", 14),
            57: ("Parte especial", 7),
            58: ("Parte especial", 10),
            62: ("Parte especial", 11),
            66: ("Parte especial", 15),
            67: ("Parte especial", 16),
            68: ("Parte especial", 17),
            72: ("Parte especial", 19),
            74: ("Parte especial", 21),
            76: ("Parte especial", 23),
            81: ("Parte general", 1),
            93: ("Parte general", 4),
            104: ("Parte general", 8),
            107: ("Parte general", 9),
        }
        for number, topic in expected.items():
            with self.subTest(question=number):
                self.assertEqual(classify("gva-c1-01-64-25", number, ""), topic)

    def test_7_22_boundary_and_budget_examples(self):
        expected = {
            1: ("Parte general", 1),
            17: ("Parte general", 8),
            34: ("Parte general", 12),
            35: ("Parte especial", 1),
            54: ("Parte especial", 11),
            64: ("Parte especial", 7),
            72: ("Parte especial", 10),
            83: ("Parte especial", 12),
            90: ("Parte especial", 13),
        }
        for number, topic in expected.items():
            with self.subTest(question=number):
                self.assertEqual(classify("gva-c1-01-7-22", number, ""), topic)


if __name__ == "__main__":
    unittest.main()
