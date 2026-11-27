import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AdminRoutingTests(unittest.TestCase):
    def test_admin_url_shows_admin_login_even_with_active_spg_session(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "reportspg.py"))
        app.query_params["page"] = "admin"
        app.session_state["logged_in"] = True
        app.session_state["admin_logged_in"] = False

        app.run()

        input_labels = [widget.label for widget in app.text_input]
        self.assertIn("Kata Sandi Admin", input_labels)
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
