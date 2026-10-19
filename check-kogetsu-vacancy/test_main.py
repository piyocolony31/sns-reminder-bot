import unittest
from datetime import date
from unittest.mock import patch
import sys
import os

# import 用パス
sys.path.append(os.path.dirname(__file__))

from main import (
    check_kogetsu_sunday_vacancies,
    get_max_search_date,
    get_target_year_months,
    EXCLUDE_MONTH_DAYS,
)


class TestKogetsuVacancyChecker(unittest.TestCase):

    def test_exclude_month_days_contains_jan_3(self):
        """1月3日が除外日に含まれることを検証"""
        self.assertIn((1, 3), EXCLUDE_MONTH_DAYS)

    def test_get_max_search_date(self):
        """基準日から7ヶ月先の月末日が正しく計算されることを検証"""
        # 10月 -> 翌年5月末 (31日)
        self.assertEqual(get_max_search_date(date(2026, 10, 19), 7), date(2027, 5, 31))
        # 5月 -> 同年12月末 (31日)
        self.assertEqual(get_max_search_date(date(2026, 5, 1), 7), date(2026, 12, 31))
        # 12月 -> 翌年7月末 (31日)
        self.assertEqual(get_max_search_date(date(2026, 12, 15), 7), date(2027, 7, 31))
        # 7月 -> 翌年2月末 (うるう年判定テスト: 2028年はうるう年なので29日)
        self.assertEqual(get_max_search_date(date(2027, 7, 1), 7), date(2028, 2, 29))

    def test_get_target_year_months(self):
        """2026-10-19 基準で、2026年12月から2027年5月までの年月リストが返ることを検証"""
        target_yms = get_target_year_months(date(2026, 10, 19))
        self.assertEqual(target_yms, ["202612", "202701", "202702", "202703", "202704", "202705"])

    @patch("main.fetch_monthly_calendar")
    def test_search_vacancies_includes_7_months_ahead(self, mock_fetch):
        """7ヶ月先 (2027年5月) の日曜日が含まれ、8ヶ月先 (2027年6月) は除外されることを検証"""
        base_date = date(2026, 10, 19)
        mock_fetch.return_value = [
            {
                "name": "露天風呂付き和室",
                "dailySalesStatusList": [
                    {
                        "salesDate": "2027-05-09",  # 日曜日、7ヶ月先
                        "salesAvailable": True,
                        "lowestPlanForRegular": {"totalPrice": 55000},
                        "stockNum": 1,
                    },
                    {
                        "salesDate": "2027-06-06",  # 日曜日、8ヶ月先（対象外）
                        "salesAvailable": True,
                        "lowestPlanForRegular": {"totalPrice": 55000},
                        "stockNum": 1,
                    },
                ],
            }
        ]

        vacancies = check_kogetsu_sunday_vacancies(base_date)
        vacancy_dates = [v["date"] for v in vacancies]

        self.assertIn("2027-05-09", vacancy_dates)
        self.assertNotIn("2027-06-06", vacancy_dates)

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

        vacancies = check_kogetsu_sunday_vacancies(date(2026, 10, 19))
        
        # 検出された空室の日付一覧を取得
        vacancy_dates = [v["date"] for v in vacancies]
        
        # 2027-01-03 は除外されているべき
        self.assertNotIn("2027-01-03", vacancy_dates)
        # 2027-01-10 は検出されているべき
        self.assertIn("2027-01-10", vacancy_dates)


if __name__ == "__main__":
    unittest.main()
