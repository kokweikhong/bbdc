import json
import requests
import pandas as pd
from datetime import datetime
import calendar
import time


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


def login():
    URL = "https://booking.bbdc.sg/bbdc-back-service/api/auth/login"
    headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
              }
    params = {
        "userId": "120W27021989",
        "userPass": "272890"
         }
    resp = requests.post(URL, headers=headers, data=json.dumps(params))
    if resp.status_code == 200:
        bearer_token = resp.json()["data"]['tokenContent']
        return bearer_token
    else:
        print("Authentication failed:", resp.text)


def get_jsessionid(token):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/account/listAccountCourseType"
    payload = r"{}"
    bearer_token = token[7:]
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'en-US,en;q=0.9',
      'Authorization': f'Bearer {str(bearer_token)}',
      'Connection': 'keep-alive',
      'Content-Type': 'application/json;charset=UTF-8',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'DNT': '1',
      'JSESSIONID': '',
      'Origin': 'https://booking.bbdc.sg',
      'Referer': 'https://booking.bbdc.sg/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
      'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200 and response.json()['success']:
        # return response.text
        auth_token = response.json()['data']['activeCourseList'][0]['authToken']
        return bearer_token, auth_token
    else:
        print("Authentication failed:", response.text)
        print(response.text)


def get_slotlist(bearer_token, auth, yy, mm):
    # url = "https://booking.bbdc.sg/bbdc-back-service/api/account/getUserProfile"
    # payload = "{}"
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c3practical/listC3PracticalSlotReleased"
    payload = {
                "courseType": "3A",
                "insInstructorId": "",
                "releasedSlotMonth": f"{str(yy)}{str(mm)}",
                "stageSubDesc": "Practical Lesson",
                "subVehicleType": None,
                "subStageSubNo": None
             }
    auth_token = auth[7:]
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'en-US,en;q=0.9',
      'Authorization': f'Bearer {str(bearer_token)}',
      'Connection': 'keep-alive',
      'Content-Type': 'application/json;charset=UTF-8',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'DNT': '1',
      'JSESSIONID': f'Bearer {str(auth_token)}',
      'Origin': 'https://booking.bbdc.sg',
      'Referer': 'https://booking.bbdc.sg/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
      'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("POST", url, headers=headers,
                                data=json.dumps(payload))
    if response.status_code == 200 and response.json()['success']:
        # return response.text
        new_data = response.json()['data']
        # df = pd.json_normalize(data, record_path=['releasedSlotListGroupByDay'])
        # print(type(df))
        return new_data
    else:
        print("Authentication failed:", response.text)
        print(response.text)
        return None


def get_mychoice(new_data, year, month):
    balance = new_data['accountBal']
    slot_list = new_data['releasedSlotListGroupByDay']
    # Create an empty DataFrame
    df = pd.DataFrame()
    # Iterate through the dictionary keys
    for key in slot_list.keys():
        # Convert the list of dictionaries to a DataFrame
        temp_df = pd.DataFrame(slot_list[key])
        # Add a new column to identify which list the data came from
        temp_df['lista'] = key
        # Append the temporary DataFrame to the main DataFrame
        df = pd.concat([df, temp_df], ignore_index=True)
    wkdays7 = df[df['slotRefName'] == 'SESSION 7']
    wkends = df[(df['lista'].isin(get_weekends(year, month))) & (df['slotRefName'] != 'SESSION 1')]
    print(wkdays7)
    my_choice = pd.concat([wkdays7, wkends], ignore_index=True)
    print(my_choice)
    chosen = my_choice[["slotId", "slotIdEnc", "bookingProgressEnc"]]
    print(chosen)
    return chosen, balance, df


def create_booking_payload(slot_id, enc_slot_id, enc_progress):
    payload = {
                "courseType": "3A",
                "slotIdList": [slot_id],
                "encryptSlotList": [
                    {
                     "slotIdEnc": f"{enc_slot_id}",
                     "bookingProgressEnc": f"{enc_progress}"
                     }],
                "insInstructorId": "",
                "subVehicleType": None}

    return payload


def submit_booking(bearer_token, auth, payload):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c3practical/callBookC3PracticalSlot"
    auth_token = auth[7:]
    headers = {
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'en-US,en;q=0.9',
      'Authorization': f'Bearer {str(bearer_token)}',
      'Connection': 'keep-alive',
      'Content-Type': 'application/json;charset=UTF-8',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'DNT': '1',
      'JSESSIONID': f'Bearer {str(auth_token)}',
      'Origin': 'https://booking.bbdc.sg',
      'Referer': 'https://booking.bbdc.sg/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
      'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"'
    }
    response = requests.request("POST", url, headers=headers,
                                data=json.dumps(payload))
    if response.status_code == 200 and response.json()['success'] == True:

        return "success"
    else:
        return "failed"


if __name__ == '__main__':
    token = login()
    print(token)
    bearer_token, auth_token = get_jsessionid(token)
    print(auth_token)
    month = 10
    year = 2023
    count = 0
    while True:
        print(count)
        new_data = get_slotlist(bearer_token, auth_token, year, str(month).zfill(2))
        count += 1
        if new_data['releasedSlotListGroupByDay'] is not None:
            chosen, balance, df = get_mychoice(new_data, year, month)
            index = 0
            while balance > 78 and not index >= len(chosen):
                # for row in chosen.itertuples():
                slot_id = chosen.loc[index, 'slotId']
                enc_slot_id = chosen.loc[index, 'slotIdEnc']
                enc_progress = chosen.loc[index, 'bookingProgressEnc']
                payload = create_booking_payload(slot_id, enc_slot_id,
                                                 enc_progress)
                print(payload)
                status = submit_booking(bearer_token, auth_token, payload)
                index += 1
                balance -= 77.76
                # send message
                success = df[df['slotId'] == slot_id]
                session = success.slotRefName
                date_ = success.slotRefDate
                start_time = success.startTime
                end_time = success.endTime
                print(f"Success: {session} {date_} {start_time} {end_time}")
            time.sleep(1)
            break
        time.sleep(1)
        if count == 10:
            break
