import unittest
from unittest.mock import patch

from schedule_entry import brands_for_team, supervisi_choices


class ScheduleOptionTests(unittest.TestCase):
    def test_brand_choices_follow_team_name(self):
        brands = [
            "Black Matcha K12",
            "Black Matcha Siro",
            "D.Super 12",
            "D.Super Kretek",
            "D.76 Apel",
            "D.76 Apel Royal",
            "Djarum 76 Aksara",
        ]

        with patch(
            "schedule_entry.read_json",
            side_effect=lambda path, fallback: brands if path == "master_brand_rokok.json" else {},
        ):
            matcha = brands_for_team("Team Matcha AA 1")
            super_team = brands_for_team("Team Super AA 1")
            apel_team = brands_for_team("Team Apel Royal AA 1")

        self.assertEqual(matcha, ["Black Matcha K12", "Black Matcha Siro"])
        self.assertEqual(super_team, ["D.Super 12", "D.Super Kretek"])
        self.assertEqual(apel_team, ["D.76 Apel", "D.76 Apel Royal"])

    @patch(
        "schedule_entry.load_master_akses",
        return_value={"supervisi_pins": {"Maya": "1234", "Rina": "5678"}},
    )
    def test_supervisor_choices_include_saved_assignments_and_access_names(self, _load_access):
        details = {
            "assignment-1": {"supervisi": "Rina"},
            "assignment-2": {"supervisi": "Dewi"},
            "assignment-3": {"supervisi": " - "},
        }

        self.assertEqual(supervisi_choices(details), ["Dewi", "Maya", "Rina"])


if __name__ == "__main__":
    unittest.main()
