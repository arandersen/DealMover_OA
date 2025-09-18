from django.test import SimpleTestCase
from core.parsing import compute_gross_profit

class GrossProfitTests(SimpleTestCase):
    def test_basic_ints(self):
        self.assertEqual(compute_gross_profit("350018", "146306"), "203712")

    def test_parentheses_already_normalized(self):
        self.assertEqual(compute_gross_profit("1000", "-200"), "1200")

    def test_decimals_strip_zeros(self):
        self.assertEqual(compute_gross_profit("1000.00", "200.50"), "799.5")

    def test_minus_zero(self):
        self.assertEqual(compute_gross_profit("0", "0"), "0")

    def test_missing_value(self):
        with self.assertRaises(ValueError):
            compute_gross_profit(None, "10")

    def test_invalid_value(self):
        with self.assertRaises(ValueError):
            compute_gross_profit("10x", "5")
