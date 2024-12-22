import unittest
from app import app

class ExpenseAppTest(unittest.TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    def test_index(self):
        responese = self.test_client.get('/')
        self.assertIn(r'<h1>List of Expenses</h1>', responese.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main()