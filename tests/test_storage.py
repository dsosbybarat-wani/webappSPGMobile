import tempfile
import unittest
from pathlib import Path

import pandas as pd

from core.storage import (
    _read_json_safe,
    _write_atomically,
    write_dataframe_atomic,
    write_json_atomic,
)


class AtomicStorageTests(unittest.TestCase):
    def test_json_cache_refreshes_after_atomic_write(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "settings.json"
            write_json_atomic(str(path), {"value": "first"})
            self.assertEqual(_read_json_safe(str(path)), {"value": "first"})

            write_json_atomic(str(path), {"value": "updated"})
            self.assertEqual(_read_json_safe(str(path)), {"value": "updated"})

    def test_failed_write_preserves_existing_file(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "data.json"
            path.write_text("original", encoding="utf-8")

            def fail_after_staging(temporary_path):
                Path(temporary_path).write_text("partial", encoding="utf-8")
                raise RuntimeError("write failed")

            with self.assertRaises(RuntimeError):
                _write_atomically(str(path), fail_after_staging)

            self.assertEqual(path.read_text(encoding="utf-8"), "original")

    def test_dataframe_csv_is_replaced_with_complete_content(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "records.csv"
            path.write_text("name\nold\n", encoding="utf-8")

            write_dataframe_atomic(pd.DataFrame({"name": ["new"]}), str(path))

            self.assertEqual(pd.read_csv(path).to_dict("records"), [{"name": "new"}])


if __name__ == "__main__":
    unittest.main()
