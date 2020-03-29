import os
import requests
from algoliasearch.search_client import SearchClient

date_fmt = "%-m/%-d/%Y"  # m/d/YYYY
days_abbrev = ["M","T","W","Th","F","Sa","S"]

report_cols = ['siteName', 'siteStatus', 'siteAddress', 'siteState', 'siteZip', 'contactPhone',
               'startDate', 'endDate', 'daysofOperation', 'breakfastTime', 'lunchTime', 'snackTimeAM',
               'snackTimePM', 'dinnerSupperTime']


class ScrapingError(Exception):
    """json data url not found in html. Possible schema change."""


def georeference_address(address):
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    data = {
        'address': address,
        'key': 'AIzaSyB5bA37UmmnyvSpvrX3t9mhuUkVTn84Rlg'
    }
    response = requests.get(url, params=data)

    if response.status_code != 200:
        return

    response = response.json()
    if not response['results']:
        return

    result = response['results'][0]  # assuming only 1 result for now
    return result['geometry']['location']


def dataframe_to_algolia(df):
    client = SearchClient.create('JWHPBFC4T1', '0d4e43a67ee4dd5d1ea7a667aded6c7e')
    index = client.init_index('us_foodbank')

    records = []
    df = df.where(pd.notnull(df), '')
    for i, row in df.iterrows():
        record = {}
        for col in report_cols:
            record[col] = row[col]

        location = georeference_address(record['siteAddress'])
        if location is None:
            print('Could not geo reference location: ({0}, {1})'.format(record['siteName'], record['siteAddress']))
            continue

        record['_geoloc'] = location

        open_times = row['breakfastTime':'dinnerSupperTime'].tolist()
        open_times = [time for time in open_times if time]
        record['openTimes'] = ', '.join(open_times)

        records.append(record)

    index.save_objects(records, {'autoGenerateObjectIDIfNotExist': True})
