import unittest

import pandas as pd

from pages.admin.records import (
    _apply_record_edit,
    _delete_record,
    _row_snapshot,
)


class AdminRecordMutationTests(unittest.TestCase):
    def setUp(self):
        self.records = pd.DataFrame(
            {
                "Waktu": ["2026-11-27 10:00", "2026-11-27 11:00"],
                "Nama": ["Nanda", "Maya"],
                "Jumlah": [5, 8],
            }
        )

    def test_edit_changes_only_selected_record(self):
        edited = self.records.loc[1].copy()
        edited["Jumlah"] = 12

        updated = _apply_record_edit(self.records, 1, edited)

        self.assertEqual(updated.loc[0, "Jumlah"], 5)
        self.assertEqual(updated.loc[1, "Jumlah"], 12)

    def test_delete_requires_unchanged_selected_record(self):
        snapshot = _row_snapshot(self.records.loc[1])
        deleted = _delete_record(self.records, 1, snapshot)

        self.assertEqual(deleted["Nama"].tolist(), ["Nanda"])
        self.assertIsNone(_delete_record(self.records, 1, ("changed",)))


if __name__ == "__main__":
    unittest.main()
