from datetime import datetime, timedelta
import calendar
import json


def get_now_with_offset(offset_hours: int = 19):
    # turn offset hours to timedelta object
    offset_td = timedelta(minutes=offset_hours)
    # utcnow is the GMT time with no offset hours
    now = datetime.now()
    return (now + offset_td).strftime('%H:%M')


def get_weekends(year=2023, month=3):
    # Set the year and month you want to get the weekends for
    # Get the calendar for the given month
    cal = calendar.monthcalendar(year, month)
    # Iterate over the weeks in the calendar
    weekends = [f'{year}-{month}-{day}' for week in cal for day in week[5:7] if day != 0]
    weekend_objects = [datetime.strptime(weekend,
                                         '%Y-%m-%d') for weekend in weekends]
    weekend_strings = [weekend_object.strftime('%Y-%m-%d %H:%M:%S') for weekend_object in weekend_objects]
    return weekend_strings


with open("config.json") as conf_file:
    config = json.load(conf_file)

TELEGRAM_TOKEN = config['telegram_token']
LOGIN_PARAMS = config['login_params']
COMMON_HEADER = config['common_header']
LOGIN_URL = config['login_url']
JSESSION_URL = config['jsession_url']
SLOTLIST_URL = config['slotlist_url']
SUBMIT_URL = config['submit_url']
DELAY = float(config['delay'])
MONTH = datetime.now().month
YEAR = datetime.now().year


if __name__ == '__main__':

    printy = MONTH
    print(printy)
    print(type(printy))

    # start = time.perf_counter()
    # url = "http://google.com"
    # post_fields = {}
    # timeout = 60
    # response = requests.post(url, data=post_fields, timeout=timeout)
    # request_time = time.perf_counter() - start
    # print("Request completed in {0:.0f}ms".format(request_time))
