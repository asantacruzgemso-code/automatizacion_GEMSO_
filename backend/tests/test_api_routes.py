import unittest

from app.main import app


class TestApiRoutes(unittest.TestCase):
    def test_testdb_route_exists(self):
        paths = {route.path for route in app.routes}
        self.assertIn("/api/testdb", paths)


if __name__ == "__main__":
    unittest.main()
