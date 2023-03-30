import json
import requests
from time import time, sleep
from utils import (LOGIN_URL, LOGIN_PARAMS, COMMON_HEADER, JSESSION_URL,
                   SLOTLIST_URL, SUBMIT_URL, MONTH, YEAR, get_weekends, DELAY,
                   WEEKEND_SESSIONS, WEEKDAY_SESSIONS)


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


def get_available_slots(new_data: dict, weekends: list):
    result_dict = new_data['releasedSlotListGroupByDay']
    key_lists = list(result_dict.keys())
    # check weekends slots
    weekends_keys = list(set(key_lists).intersection(set(weekends)))
    weekends_dict = {k: result_dict[k] for k in weekends_keys
                     if k in result_dict}
    weekends_slots = [tuple([slot['slotId'], slot['slotIdEnc'],
                            slot['bookingProgressEnc']])
                      for slots in weekends_dict.values()
                      for slot in slots
                      if slot['slotRefName'] in WEEKEND_SESSIONS]

    # check weekdays slots
    weekdays_keys = list(set(key_lists) - set(weekends))
    weekdays_dict = {k: result_dict[k] for k in weekdays_keys
                     if k in result_dict}
    weekdays_slots = [tuple([slot['slotId'], slot['slotIdEnc'],
                            slot['bookingProgressEnc']])
                      for slots in weekdays_dict.values()
                      for slot in slots
                      if slot['slotRefName'] in WEEKDAY_SESSIONS]
    available_slots = weekdays_slots + weekends_slots
    return available_slots, new_data['accountBal']


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
                available_slots, balance = get_available_slots(new_data,
                                                               weekends)
                if available_slots and balance > 78:
                    message = ""
                    for slot in available_slots:
                        payload = create_booking_payload(slot[0], slot[1],
                                                         slot[2])
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
                        message += f"{success}|{session}|{date_}|"
                        if balance < 78:
                            return f"{message}.Balance is not enough! {balance}. Please top up."
                    return message
                sleep(1)
                break
            sleep(DELAY)
        except Exception as err:
            return f"{err}"
    return f"Unable find appropriate bookings. Balance:{balance_}"


if __name__ == '__main__':
    print(check_and_book_slot())
