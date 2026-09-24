import unittest
from datetime import date
from unittest.mock import patch
import sys
import os

# import 用パス
sys.path.append(os.path.dirname(__file__))

from main import check_kogetsu_sunday_vacancies, EXCLUDE_MONTH_DAYS


class TestKogetsuVacancyChecker(unittest.TestCase):

    def test_exclude_month_days_contains_jan_3(self):
        """1月3日が除外日に含まれることを検証"""
        self.assertIn((1, 3), EXCLUDE_MONTH_DAYS)

    @patch("main.fetch_monthly_calendar")
    def test_jan_3_vacancy_is_skipped(self, mock_fetch):
        """2027年1月3日(日)の空室がスキップされることを検証"""
        mock_fetch.return_value = [
            {
                "name": "露天風呂付き和室",
                "dailySalesStatusList": [
                    {
                        "salesDate": "2027-01-03",
                        "salesAvailable": True,
                        "lowestPlanForRegular": {"totalPrice": 50000},
                        "stockNum": 1,
                    },
                    {
                        "salesDate": "2027-01-10",
                        "salesAvailable": True,
                        "lowestPlanForRegular": {"totalPrice": 50000},
                        "stockNum": 1,
                    },
                ],
            }
        ]

        vacancies = check_kogetsu_sunday_vacancies()
        
        # 検出された空室の日付一覧を取得
        vacancy_dates = [v["date"] for v in vacancies]
        
        # 2027-01-03 は除外されているべき
        self.assertNotIn("2027-01-03", vacancy_dates)
        # 2027-01-10 は検出されているべき
        self.assertIn("2027-01-10", vacancy_dates)


if __name__ == "__main__":
    unittest.main()
