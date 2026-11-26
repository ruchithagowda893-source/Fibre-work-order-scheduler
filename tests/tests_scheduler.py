import unittest
from src.scheduler import Scheduler


class TestScheduler(unittest.TestCase):

    def setUp(self):
        self.scheduler = Scheduler()

    def test_scheduler_initialization(self):
        self.assertIsNotNone(self.scheduler)

    def test_scheduler_has_technicians(self):
        self.assertIsInstance(self.scheduler.technicians, list)

    def test_scheduler_has_zones(self):
        self.assertIsInstance(self.scheduler.zones, dict)

    def test_scheduler_has_work_orders(self):
        self.assertIsInstance(self.scheduler.work_orders, list)

    def test_scheduler_has_assignments(self):
        self.assertIsInstance(self.scheduler.assignments, list)

    def test_scheduler_has_unassigned(self):
        self.assertIsInstance(self.scheduler.unassigned, list)

    def test_scheduler_has_errors(self):
        self.assertIsInstance(self.scheduler.errors, list)

    def test_load_zones_method(self):
        self.assertTrue(callable(self.scheduler.load_zones))

    def test_load_technicians_method(self):
        self.assertTrue(callable(self.scheduler.load_technicians))

    def test_load_work_orders_method(self):
        self.assertTrue(callable(self.scheduler.load_work_orders))

    def test_schedule_method(self):
        self.assertTrue(callable(self.scheduler.schedule))


if __name__ == "__main__":
    unittest.main()