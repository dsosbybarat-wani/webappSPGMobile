import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import requests

from core.supabase_sync import (
    enqueue_supabase_entry,
    flush_supabase_entry_queue,
    pending_supabase_entry_count,
)


class SupabaseEntrySyncTests(unittest.TestCase):
    def test_enqueue_stores_new_entry_with_unique_id(self):
        with TemporaryDirectory() as temporary_directory:
            queue_path = str(Path(temporary_directory) / "queue.json")

            first_id = enqueue_supabase_entry(
                "spg_sale", {"Nama_Konsumen": "A"}, queue_path=queue_path
            )
            second_id = enqueue_supabase_entry(
                "supervisor_report", {"Warkop_LKK": "B"}, queue_path=queue_path
            )

            queue = json.loads(Path(queue_path).read_text(encoding="utf-8"))
            self.assertNotEqual(first_id, second_id)
            self.assertEqual(pending_supabase_entry_count(queue_path), 2)
            self.assertEqual([entry["id"] for entry in queue], [first_id, second_id])

    @patch(
        "core.supabase_sync.get_supabase_config",
        return_value=("https://example.supabase.co", "secret"),
    )
    @patch("core.supabase_sync.requests.post")
    def test_failed_delivery_keeps_entry_queued_and_retry_deduplicates(
        self, post, _get_supabase_config
    ):
        with TemporaryDirectory() as temporary_directory:
            queue_path = str(Path(temporary_directory) / "queue.json")
            entry_id = enqueue_supabase_entry(
                "spg_sale", {"Nama_Konsumen": "A"}, queue_path=queue_path
            )
            post.side_effect = requests.ConnectionError("offline")

            with self.assertRaises(RuntimeError):
                flush_supabase_entry_queue(queue_path=queue_path)
            self.assertEqual(pending_supabase_entry_count(queue_path), 1)

            response = MagicMock()
            response.raise_for_status.return_value = None
            post.side_effect = None
            post.return_value = response
            self.assertEqual(flush_supabase_entry_queue(queue_path=queue_path), 1)

            self.assertEqual(pending_supabase_entry_count(queue_path), 0)
            self.assertEqual(post.call_args.kwargs["json"][0]["id"], entry_id)
            self.assertEqual(
                post.call_args.args[0],
                "https://example.supabase.co/rest/v1/app_entries",
            )
            self.assertEqual(
                post.call_args.kwargs["headers"]["Prefer"],
                "resolution=ignore-duplicates,return=minimal",
            )


if __name__ == "__main__":
    unittest.main()
