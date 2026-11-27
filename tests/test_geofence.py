import unittest

from shapely.geometry import Point

from geo.loader import is_point_within_city


class CityGeofenceTests(unittest.TestCase):
    def test_reported_surabaya_coordinate_is_inside_city_boundary(self):
        point = Point(112.696090, -7.259055)

        self.assertTrue(is_point_within_city("Surabaya", point))

    def test_point_outside_city_boundary_is_rejected(self):
        point = Point(112.0, -7.25)

        self.assertFalse(is_point_within_city("Surabaya", point))


if __name__ == "__main__":
    unittest.main()
