import re
import json
import requests
from lxml import etree
import dateparser
import pandas as pd
from datetime import timedelta

from scrapers.utils import ScrapingError, days_abbrev, date_fmt


class Idaho:
    def __init__(self):
        self.df = None
        self.new_cols = ['hasBreakfast','hasLunch','hasSnackAM', 'hasSnackPM', 'hasDinnerSupper']

    def scrape(self):
        print("scraping....")
        data = Scraper.scrape()
        print("loading data....")
        self.df = self._load_dataframe(data)
        print("processing data....")
        self._process_df()
        return self.df

    def _load_dataframe(self, data):
        df = pd.DataFrame(data['dataRS'], columns=data['columnNames'])
        col_map = {'Meal Service Address': 'siteAddress',
                   'City': 'siteCity',
                   'State': 'siteState',
                   'Zipcode': 'siteZip',
                   'Name of Meal Service Location': 'siteName',
                   'Phone Number': 'contactPhone',
                   'Type of Meals Served': 'mealTypes',
                   'Service Dates': 'serviceDates'
                   }
        df.columns = df.columns.map(col_map)
        req_cols = ['startDate', 'endDate', 'daysofOperation', 'breakfastTime',
                    'lunchTime', 'snackTimeAM', 'snackTimePM', 'dinnerSupperTime',
                    "siteStatus"]
        new_cols = ['hasBreakfast', 'hasLunch', 'hasSnackAM', 'hasSnackPM', 'hasDinnerSupper']
        for col in req_cols + new_cols:
            df[col] = None

        return df

    def _process_df(self):
        self.df = self.df.apply(SiteDetails.process, axis=1)
        self.df = self.df.apply(MealTypes.process, axis=1)
        self.df = self.df.apply(ServiceDates.process, axis=1)
        self.df.startDate = self.df.startDate.dt.strftime(date_fmt)
        self.df.endDate = self.df.endDate.dt.strftime(date_fmt)
        self.df.daysofOperation = self.df.daysofOperation.apply(lambda x: ",".join(x))



# if not capitalize, we'll just use UPPERCASE
if days_abbrev == [d.capitalize() for d in days_abbrev]:
    capitalize = True
else:
    capitalize = False


class Scraper:
    URL = 'https://batchgeo.com/map/3195baf394a7f7db04ce06c69b17842f'

    @classmethod
    def scrape(cls):
        html = cls.make_request(cls.URL)
        json_url = cls._find_json_url(html)
        if not json_url:
            raise ScrapingError()

        script_data = cls.make_request(json_url)
        return cls._load_as_json_data(script_data)

    def make_request(url):
        headers = {
            'authority': 'batchgeo.com',
            'cache-control': 'max-age=0',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
            'sec-fetch-dest': 'document',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'accept-language': 'en-US,en;q=0.9',
        }

        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.text

    @staticmethod
    def _load_as_json_data(text):
        skip_chars = "per = "
        n = len(skip_chars)
        data = json.loads(text[n:-1])
        return data

    @staticmethod
    def _find_json_url(html):
        tree = etree.HTML(html)
        src_url = tree.xpath(".//script[contains(@src,'map/json')]")
        if src_url is not None:
            src_url = src_url[0]
            src_url = src_url.get('src')
            # check if it just needs http
            if src_url.startswith("//"):
                src_url = "https:" + src_url
            # check if it's a relative path
            elif src_url.startswith("/"):
                src_url = "https://batchgeo.com" + src_url
        return src_url

class BaseParser:
    sort_abbrev = days_abbrev.copy()
    # double it so we can go from Thursday - Monday
    days_abbrev *= 2

    @classmethod
    def _clean_and_sort_days_of_op(cls, days_of_op: list) -> list:
        """removes any duplicates from list and orders them according to the days_abbrev"""

        if capitalize:
            days_of_op = [d.capitalize() for d in days_of_op]
        else:
            days_of_op = [d.upper() for d in days_of_op]

        days_of_op = list(set(days_of_op))
        try:
            days_of_op.sort(key=cls.sort_abbrev.index)
        except ValueError:
            # means day isn't in the abbrev, so just return it
            pass
        return days_of_op


class MealTypes(BaseParser):
    brekkie_p = re.compile("breakfast", flags=re.I)
    lunch_p = re.compile("lunch", flags=re.I)
    snack_p = re.compile("snack", flags=re.I)
    dinner_p = re.compile("(?:supper)|(?:dinner)", flags=re.I)
    days_p = re.compile(r"\s([a-z]{1,2}-[a-z]{1,2})")

    @classmethod
    def process(cls, row):
        d = cls._parse_meal_types(row['mealTypes'])
        days_of_op = row['daysofOperation']
        for k, v in d.items():
            if k == "daysofOperation" and days_of_op:
                days_of_op.extend(row['daysofOperation'])
            else:
                row[k] = v
        if days_of_op:
            row['daysofOperation'] = cls._clean_and_sort_days_of_op(days_of_op)
        return row

    @classmethod
    def _parse_meal_types(cls, meal_types: str) -> {}:
        d = {}
        meal_types = meal_types.lower()

        # if it has times, they're split like
        # Breakfast: 7:30 AM - 9:00 AM; Lunch: 11 AM - 12:30 PM
        meal_times = cls._get_meal_times(meal_types)
        if meal_times:
            d.update(meal_times)

        if re.search(cls.brekkie_p, meal_types):
            d['hasBreakfast'] = True

        if re.search(cls.lunch_p, meal_types):
            d['hasLunch'] = True

        if re.search(cls.snack_p, meal_types):
            # check if it's listed before or after lunch
            if meal_types.find("snack") > meal_types.find("lunch"):
                d['hasSnackPM'] = True
            else:
                d['hasSnackAM'] = True

        if re.search(cls.dinner_p, meal_types):
            d['hasDinnerSupper'] = True

        days_of_op = cls.extract_days_from_meal_types(meal_types)
        if days_of_op:
            d['daysofOperation'] = cls._clean_and_sort_days_of_op(days_of_op)

        return d

    @classmethod
    def _extract_day_range(cls, text: str) -> {}:
        """Searches for day of the weeks in a range.
        Example
        >>> _extract_day_range("Lunch M-TH")
        ['M', 'T', 'W', 'Th']
        """
        text = text.lower()
        # use this one for index lookup
        abbrevs = [d.lower() for d in cls.days_abbrev]

        days_range_p = re.compile(r"(\b[a-z]{1,2})(?:\s?\-\s?)(\b[a-z]{1,2})", flags=re.I)
        m = re.search(days_range_p, text)
        if m:
            days = m.groups(0)
            # Should only come from days like M-TH
            assert len(days) == 2, "More than 2 days found in range"
            start, end = days
            start_ix = abbrevs.index(start)
            end_ix = abbrevs.index(end)

            # check if day range is not ordinal, maybe Th-M
            if start_ix > end_ix:
                end_ix += 8
            else:
                end_ix += 1
            return cls.days_abbrev[start_ix:end_ix]
        return []

    @staticmethod
    def _extract_explict_days(text: str) -> {}:
        """Searches for day of the weeks.
        Example
        >>> _extract_day_range("Lunch M,W,F")
        ['M', 'W', 'F']
        """
        text = text.lower()

        days_p = re.compile(r"(\b[a-z]{1,2})(?:\s|\-|\,|\b)", flags=re.I)
        days = re.findall(days_p, text) or []
        days = [d for d in days if d.lower() not in ["am", "pm"]]

        return days

    @classmethod
    def extract_days_from_meal_types(cls, meal_types):
        # check for range first
        days = cls._extract_day_range(meal_types)
        if not days:
            days = cls._extract_explict_days(meal_types)
        return days

    @classmethod
    def _get_meal_times(cls, meal_types: str) -> {}:
        """Gets meals and times from string.
        Example:
        >>> _get_meal_times('Breakfast: 7:30 AM - 9:00 AM; Lunch: 11:00 AM - 12:30 PM')
        {'breakfastTime': '7:30 AM - 9:00 AM', 'lunchTime': '11:00 AM - 12:30 PM'}
        """
        d = {}

        time_pattern = re.compile("(\w+)\:\s(\d{1,2}(?:\:\d{2})?\s*[A|P]M\s*\-\s*\d{1,2}(?:\:\d{2})\s*[A|P]M)",
                                  flags=re.I)
        matches = re.findall(time_pattern, meal_types)

        for match in matches:
            meal, time = match
            time = time.upper()
            if re.search(cls.brekkie_p, meal):
                d['breakfastTime'] = time
            if re.search(cls.lunch_p, meal):
                d['lunchTime'] = time
            if re.search(cls.snack_p, meal):
                if time.find("AM") > -1:
                    d['snackTimeAM'] = time
                if time.find("PM") > -1:
                    d['snackTimePM'] = time
            if re.search(cls.dinner_p, meal):
                d['dinnerSupperTime'] = time
        return d


class ServiceDates(BaseParser):
    abbrevs = days_abbrev.copy() * 2

    @classmethod
    def process(cls, row):
        start_dates = []
        end_dates = []
        days_of_op = []

        date_text = row['serviceDates']
        date_text = date_text.replace("\xa0", " ")

        # check for multiple dates split by ;
        splits = date_text.split(";")
        for split in splits:
            d = cls.parse_date(split)
            if d.get("daysofOperation", []):
                days_of_op.extend(d.get('daysofOperation'))
            if d.get('startDate'):
                start_dates.append(d.get('startDate'))
            if d.get('endDate'):
                end_dates.append(d.get('endDate'))

        row['startDate'] = min(start_dates) if start_dates else None
        row['endDate'] = max(end_dates) if end_dates else None
        row['daysofOperation'] = cls._clean_and_sort_days_of_op(days_of_op)

        return row

    @classmethod
    def check_date_range(cls, date_text: str) -> {}:
        """Parses March 23-26 into two start and stop dates"""
        d = {}
        dates_range_p = re.compile(r"(?P<month>\w+)\s(?P<start>\d+)\s?\-\s?(?P<end>\d+|(?:tbd))", flags=re.I)
        m = re.search(dates_range_p, date_text)
        if m:
            gd = m.groupdict()
            start = f"{gd['month']} {gd['start']}"
            d['startDate'] = dateparser.parse(start)

            if gd['end'].upper() != "TBD":
                end = f"{gd['month']} {gd['end']}"
                d['endDate'] = dateparser.parse(end)
        return d

    @classmethod
    def parse_date(cls, date_text: str) -> {}:
        d = {}
        dates_p = re.compile(r"(?P<start>\w+\s\d{1,2})\s?\-\s?(?P<end>\w+\s\d*)(?:\s?\((?P<days>\w+\s?\-\s?\w+)\))?")

        # check for dates like March 20-23
        d = cls.check_date_range(date_text)
        if not d:
            # check for normal date like March 23 - April 12
            m = re.search(dates_p, date_text)
            if m:
                gd = m.groupdict()
                start = gd.get('start')
                end = gd.get('end')
                d['startDate'] = dateparser.parse(start)
                d['endDate'] = dateparser.parse(end)
                d['daysofOperation'] = gd['days']
        if d.get('daysofOperation'):
            d['daysofOperation'] = cls.convert_days_of_operation(d['daysofOperation'])

        start = d.get('startDate')
        end = d.get('endDate')

        if start and end:
            # check if Dec - Jan
            if start.month > end.month and start.year == end.year:
                end = end + timedelta(year=1)
                d.update({"end": end})

        return d

    @classmethod
    def convert_days_of_operation(cls, days_text):
        """Converts Monday-Sunday to M,T,W,Th,F,Sa,S format"""
        abbrevs = cls.abbrevs.copy()

        start, end = days_text.split("-")
        start = dateparser.parse(start)
        if start:
            # returns the index of the day of the week. Monday = 0
            start = start.weekday()

        end = dateparser.parse(end)
        if end:
            end = end.weekday()
        if start is not None and end is not None:
            # check to see if dates are reversed as in Monday-Sunday
            if start > end:
                abbrevs *= 2
                return abbrevs[start:end + 8]
            else:
                return abbrevs[start:end + 1]

class SiteDetails:

    @classmethod
    def process(cls, row):
        row = cls._create_address(row)
        row = cls._clean_phone(row)
        return row

    @staticmethod
    def _create_address(row):
        row['siteAddress'] = f"{row['siteAddress']} {row['siteCity']}, {row['siteState']} {row['siteZip']}"
        return row

    @staticmethod
    def _clean_phone(row):
        row['contactPhone'] = "".join(re.findall("\d", row['contactPhone']))
        return row


