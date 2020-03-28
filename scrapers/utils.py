import os
date_fmt = "%-m/%-d/%Y"  # m/d/YYYY
days_abbrev = ["M","T","W","Th","F","Sa","S"]

report_cols = ['siteName', 'siteStatus', 'siteAddress', 'siteState', 'siteZip', 'contactPhone',
               'startDate', 'endDate', 'daysofOperation', 'breakfastTime', 'lunchTime', 'snackTimeAM',
               'snackTimePM', 'dinnerSupperTime']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ScrapingError(Exception):
    """json data url not found in html. Possible schema change."""





