import unittest

from domain.target import clean_brand_target_name, get_target_for_brand


class TargetGroupTests(unittest.TestCase):
    def test_apel_variants_share_group_name_and_target(self):
        apel_target = get_target_for_brand("D.76 Apel", "target_team", 50)
        royal_target = get_target_for_brand("D.76 Apel Royal", "target_team", 50)

        self.assertEqual(
            clean_brand_target_name("D.76 Apel"),
            "D.76 Apel & Apel Royal (Gabungan)",
        )
        self.assertEqual(
            clean_brand_target_name("D.76 Apel Royal"),
            "D.76 Apel & Apel Royal (Gabungan)",
        )
        self.assertEqual(apel_target, royal_target)


if __name__ == "__main__":
    unittest.main()
