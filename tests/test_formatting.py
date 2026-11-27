import unittest

import pandas as pd

from ui.components import format_indonesian_number, format_sales_table


class SalesTableFormattingTests(unittest.TestCase):
    def test_formats_integer_and_decimal_values_in_indonesian_style(self):
        self.assertEqual(format_indonesian_number(3_000_000), "3.000.000")
        self.assertEqual(format_indonesian_number(1234.5), "1.234,5")

    def test_formats_sales_columns_without_mutating_the_data(self):
        dataframe = pd.DataFrame(
            {
                "Jumlah_Bungkus": [3_000_000],
                "Koordinat": [106.812345],
            }
        )

        styled = format_sales_table(dataframe).to_html()

        self.assertIn("3.000.000", styled)
        self.assertIn("106.812345", styled)
        self.assertEqual(dataframe.loc[0, "Jumlah_Bungkus"], 3_000_000)


if __name__ == "__main__":
    unittest.main()
