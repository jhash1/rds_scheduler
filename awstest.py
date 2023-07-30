import unittest
from aws import AWSCostExplorer

class TestCostExplorer(unittest.TestCase):
    def test_ce(self):
        ce_class = AWSCostExplorer()
        result = ce_class.return_monthly_rds_cost_costexplorer()
        self.assertEqual(result,"1")

if __name__ == '__main__':
    unittest.main()