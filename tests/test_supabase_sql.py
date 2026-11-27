import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from core.supabase_sql import execute_supabase_sql, split_sql_statements


class SupabaseSqlTests(unittest.TestCase):
    def test_splits_script_without_breaking_semicolons_inside_strings(self):
        statements = split_sql_statements(
            "SELECT 'left;right';\n-- restore step\nINSERT INTO demo VALUES ('x;y');"
        )

        self.assertEqual(len(statements), 2)
        self.assertIn("'left;right'", statements[0])
        self.assertIn("'x;y'", statements[1])

    def test_rejects_empty_script(self):
        with self.assertRaises(ValueError):
            split_sql_statements(" -- nothing to run\n ; ")

    @patch("core.supabase_sql.get_supabase_database_url", return_value="postgresql://test")
    @patch("psycopg.connect")
    def test_executes_query_and_returns_rows(self, connect, _get_database_url):
        connection = MagicMock()
        cursor = MagicMock()
        connection.__enter__.return_value = connection
        connection.cursor.return_value.__enter__.return_value = cursor
        cursor.description = [SimpleNamespace(name="answer")]
        cursor.fetchmany.return_value = [(42,)]
        cursor.rowcount = 1
        connect.return_value = connection

        results = execute_supabase_sql("SELECT 42")

        self.assertEqual(results[0]["columns"], ["answer"])
        self.assertEqual(results[0]["rows"], [(42,)])
        self.assertFalse(results[0]["truncated"])


if __name__ == "__main__":
    unittest.main()
