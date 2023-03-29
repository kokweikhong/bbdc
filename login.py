import json
import requests
import pandas as pd
from time import time, sleep
from utils import (LOGIN_URL, LOGIN_PARAMS, COMMON_HEADER, JSESSION_URL,
                   SLOTLIST_URL, SUBMIT_URL, MONTH, YEAR, get_weekends, DELAY)


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
    payload = {}
    bearer_token = token[7:]
    headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': '',
      **COMMON_HEADER
    }
    response = requests.post(JSESSION_URL, headers=headers,
                             json=payload)
    response.raise_for_status()
    auth_token = response.json()['data']['activeCourseList'][0]['authToken']
    return bearer_token, auth_token


def get_slotlist(bearer_token: str, auth: str, yy: int, mm: int):
    payload = {
                "courseType": "3A",
                "insInstructorId": "",
                "releasedSlotMonth": f"{str(yy)}{str(mm)}",
                "stageSubDesc": "Practical Lesson",
                "subVehicleType": None,
                "subStageSubNo": None
             }
    headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': f'Bearer {auth[7:]}',
      **COMMON_HEADER
    }
    response = requests.post(SLOTLIST_URL, headers=headers,
                             json=payload)
    response.raise_for_status()
    return response.json()["data"]


def get_mychoice(new_data: dict):
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


def create_booking_payload(slot_id: str, enc_slot_id: str, enc_progress: str):
    return {
        "courseType": "3A",
        "slotIdList": [slot_id],
        "encryptSlotList": [
            {"slotIdEnc": enc_slot_id, "bookingProgressEnc": enc_progress}
        ],
        "insInstructorId": "",
        "subVehicleType": None,
    }


def submit_booking(bearer_token: str, auth: str, payload: dict):
    headers = {
      'Authorization': f'Bearer {bearer_token}',
      'Cookie': f'bbdc-token=Bearer%20{bearer_token}',
      'JSESSIONID': f'Bearer {auth[7:]}',
      **COMMON_HEADER
    }
    response = requests.post(SUBMIT_URL, headers=headers, json=payload)
    if response.json().get("success"):
        return "success", response.json()["data"]
    return "failed", None


def check_and_book_slot(minutes=19):
    token = login()
    bearer_token, auth_token = get_jsessionid(token)
    weekends = get_weekends(YEAR, MONTH)
    t_end = time() + 60 * minutes
    balance_ = ""
    while time() < t_end:
        try:
            # Get the latest slot list data
            new_data = get_slotlist(bearer_token, auth_token,
                                    YEAR, str(MONTH).zfill(2))
            balance_ = new_data['accountBal']
            # Check if any slots are available
            if new_data['releasedSlotListGroupByDay'] is not None:
                # Get the first available slot
                temp = iter(new_data['releasedSlotListGroupByDay'].values())
                first_slot = next(temp)[0]
                slot_name = first_slot['slotRefName']
                slot_date = first_slot['slotRefDate']

                # Check if the slot is valid (on a weekend or session 7)
                if slot_name == "SESSION 7" or slot_date in weekends:
                    # Try to book the slot
                    chosen_slots, balance, df = get_mychoice(new_data)
                    for index, row in chosen_slots.iterrows():
                        if balance < 78 or index >= len(chosen_slots):
                            break
                        # for row in chosen.itertuples():
                        slot_id = row['slotId'].item()
                        enc_slot_id = row['slotIdEnc']
                        enc_progress = row['bookingProgressEnc']
                        payload = create_booking_payload(slot_id, enc_slot_id,
                                                         enc_progress)
                        # print(payload)
                        status, data = submit_booking(bearer_token, auth_token,
                                                      payload)
                        if status == "failed":
                            raise Exception("Failed to book.")
                        balance -= 77.76
                        # send message
                        data_list = data['bookedPracticalSlotList'][0]
                        success = str(data_list['message'])
                        session = str(data_list['slotRefName'])
                        date_ = str(data_list['slotRefDate'])
                        start_time = str(data_list['startTime'])
                        end_time = str(data_list['endTime'])
                        message = f"{success}|{session}|{date_}|{start_time}|"\
                                  f"{end_time}|{balance}"
                        return message
                    sleep(1)
                    break
            sleep(DELAY)
        except Exception as err:
            print(err)
            return f"{err}"
    return f"Unable find appropriate bookings. Balance:{balance_}"


if __name__ == '__main__':
    print(check_and_book_slot())
