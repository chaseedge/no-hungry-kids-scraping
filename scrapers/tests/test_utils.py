import datetime
from unittest import TestCase

from scrapers.utils import convert_start_end_dates, extract_explict_days, extract_meal_times, extract_month_day_range, extract_weekday_range, clean_and_sort_days_list


class TestUtils(TestCase):

    def test_get_meal_times(self):
        # should extract meal and the times from the string
        tests_get_meal_times = [
            [
                'Breakfast: 7:30 AM - 9:00 AM; Lunch: 11:00 AM - 12:30 PM',
                {'breakfastTime': '7:30 AM - 9:00 AM', 'lunchTime': '11:00 AM - 12:30 PM'}
            ],
            [
                'Breakfast: 7:30AM - 9:00AM',
                {'breakfastTime': '7:30AM - 9:00AM'}
            ],
            [
                'Dinner: 5PM',
                {"dinnerSupperTime": "5PM"}
            ]
        ]
        for test in tests_get_meal_times:
            result = extract_meal_times(test[0])
            self.assertTrue(result == test[1])


    def test_extract_month_day_range(self):
        test_dict = {
            "March 23-26": [datetime.datetime(2020, 3, 23), datetime.datetime(2020, 3, 26)],
            "March 23-April 26": [datetime.datetime(2020, 3, 23), datetime.datetime(2020, 4, 26)],
            "Jan 23-April 26": [datetime.datetime(2020, 1, 23), datetime.datetime(2020, 4, 26)],
            "Dec 23-April 26": [datetime.datetime(2020, 12, 23), datetime.datetime(2021, 4, 26)],
        }

        for k, v in test_dict.items():
            dates = extract_month_day_range(k)
            self.assertTrue(dates[0] == v[0])
            self.assertTrue(dates[1] == v[1])

    def test_clean_and_sort_days_list(self):
        tests_clean_and_sort_days_list = [
            (["T", "M", "S"], "M,T,S"),
            (["T", "T", "S"], "T,S"),
            (["S", "M", "S"], "M,S"),
        ]
        for test in tests_clean_and_sort_days_list:
            result = clean_and_sort_days_list(test[0])
            self.assertEqual(result, test[1])
