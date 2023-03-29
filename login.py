import json
import utils
import requests
import pandas as pd
import time
from utils import (
    LOGIN_URL, LOGIN_PARAMS, COMMON_HEADER, JSESSION_URL,
    SLOTLIST_URL, SUBMIT_URL, MONTH, YEAR, get_weekends
)


def login() -> str:
    headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
              }
    resp = requests.post(LOGIN_URL, headers=headers,
                         data=json.dumps(LOGIN_PARAMS))
    resp.raise_for_status()
    return resp.json()["data"]['tokenContent']


def get_jsessionid(token: str):
    payload = r"{}"
    bearer_token = token[7:]
    unique_headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': '',
    }
    headers = {**unique_headers, **COMMON_HEADER}
    response = requests.request("POST", JSESSION_URL, headers=headers,
                                data=payload)
    if response.status_code == 200 and response.json()['success']:
        # return response.text
        auth_token = response.json()['data']['activeCourseList'][0]['authToken']
        return bearer_token, auth_token
    else:
        raise Exception(f"JSession failed: {response.text}")


def get_slotlist(bearer_token, auth, yy, mm):
    payload = {
                "courseType": "3A",
                "insInstructorId": "",
                "releasedSlotMonth": f"{str(yy)}{str(mm)}",
                "stageSubDesc": "Practical Lesson",
                "subVehicleType": None,
                "subStageSubNo": None
             }
    auth_token = auth[7:]
    unique_headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': f'Bearer {auth_token}',
    }
    headers = {**unique_headers, **COMMON_HEADER}
    response = requests.request("POST", SLOTLIST_URL, headers=headers,
                                data=json.dumps(payload))
    if response.status_code == 200 and response.json()['success']:
        new_data = response.json()['data']
        return new_data
    else:
        raise Exception(f"Slotlist failed: {response.text}")


def get_mychoice(new_data):
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
    weekends = get_weekends(YEAR, MONTH)
    mask = df['lista'].isin(weekends) & df['slotRefName'] != 'SESSION 1'
    wkends = df[mask]
    my_choice = pd.concat([wkdays7, wkends], ignore_index=True)
    chosen = my_choice[["slotId", "slotIdEnc", "bookingProgressEnc"]]
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
    auth_token = auth[7:]
    unique_headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': f'Bearer {auth_token}',
    }
    headers = {**unique_headers, **COMMON_HEADER}
    response = requests.request("POST", SUBMIT_URL,
                                headers=headers,
                                data=json.dumps(payload))

    if response.status_code == 200 and response.json()['success']:
        return "success", response.json()['data']
    else:
        return "failed", None


def extract(minutes=19):
    token = login()
    bearer_token, auth_token = get_jsessionid(token)
    weekends = get_weekends(YEAR, MONTH)
    # count = 0
    # while True:
    t_end = time.time() + 60 * minutes
    balance_ = ""
    while time.time() < t_end:
        # print(count)
        # count += 1
        try:
            new_data = get_slotlist(bearer_token, auth_token, 
                                    YEAR, str(MONTH).zfill(2))
            balance_ = new_data['accountBal']
            # print(new_data)
            if new_data['releasedSlotListGroupByDay'] is not None:
                check = next(iter(new_data['releasedSlotListGroupByDay'].values()))[0]
                check_val = check['slotRefName']
                check_date = check['slotRefDate']
                if check_val == "SESSION 7" or check_date in weekends:
                    chosen, balance, df = get_mychoice(new_data)
                    index = 0
                    while balance > 78 and not index >= len(chosen):
                        # for row in chosen.itertuples():
                        slot_id = chosen.loc[index, 'slotId'].item()
                        # print(slot_id)
                        enc_slot_id = chosen.loc[index, 'slotIdEnc']
                        enc_progress = chosen.loc[index, 'bookingProgressEnc']
                        payload = create_booking_payload(slot_id, enc_slot_id,
                                                         enc_progress)
                        # print(payload)
                        status, data = submit_booking(bearer_token, auth_token,
                                                      payload)
                        if status == "failed":
                            return "Failed to book."
                            break
                        index += 1
                        balance -= 77.76
                        # send message
                        data_list = data['bookedPracticalSlotList'][0]
                        success = str(data_list['message'])
                        session = str(data_list['slotRefName'])
                        date_ = str(data_list['slotRefDate'])
                        start_time = str(data_list['startTime'])
                        end_time = str(data_list['endTime'])
                        message = f"{success}|{session}|{date_}|{start_time}|{end_time}|{balance}"
                        print(message)
                        # print(data)
                        return message
                    time.sleep(1)
                    break
            time.sleep(utils.delay)
        except Exception as err:
            print(err)
            return f"{err}"

        # if count == 20:
        #     break
    return f"Unable find appropriate bookings. Balance:{balance_}"


if __name__ == '__main__':
    print(extract())
