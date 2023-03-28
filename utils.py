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
    weekends = []
    for week in cal:
        # Check if Saturday or Sunday is in the week
        if week[5] != 0:
            # Saturday is in the week
            sat = f'{year}-{month}-{week[5]}'
            sat_object = datetime.strptime(sat, '%Y-%m-%d')
            weekends.append(sat_object.strftime("%Y-%m-%d %H:%M:%S"))
        if week[6] != 0:
            # Sunday is in the week
            sun = f'{year}-{month}-{week[6]}'
            sun_object = datetime.strptime(sun, '%Y-%m-%d')
            weekends.append(sun_object.strftime("%Y-%m-%d %H:%M:%S"))
    return weekends


with open("config.json") as conf_file:
    config = json.load(conf_file)

telegram_token = config['telegram_token']
login_params = config['login_params']
common_header = config['common_header']
login_url = config['login_url']
jsession_url = config['jsession_url']
slotlist_url = config['slotlist_url']
submit_url = config['submit_url']


if __name__ == '__main__':
    printy = login_params
    print(printy)
    print(type(printy))

    # start = time.perf_counter()
    # url = "http://google.com"
    # post_fields = {}
    # timeout = 60
    # response = requests.post(url, data=post_fields, timeout=timeout)
    # request_time = time.perf_counter() - start
    # print("Request completed in {0:.0f}ms".format(request_time))
