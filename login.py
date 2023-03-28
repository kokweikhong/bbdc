import json
import utils
import requests
import pandas as pd
import time


common_header = utils.common_header


def login():
    URL = utils.login_url
    headers = {
                "accept": "application/json",
                "Content-Type": "application/json"
              }
    params = utils.login_params

    resp = requests.post(URL, headers=headers, data=json.dumps(params))
    if resp.status_code == 200:
        bearer_token = resp.json()["data"]['tokenContent']
        return bearer_token
    else:
        print("Authentication failed:", resp.text)


def get_jsessionid(token):
    url = utils.jsession_url
    payload = r"{}"
    bearer_token = token[7:]
    unique_headers = {
      'Authorization': f'Bearer {str(bearer_token)}',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'JSESSIONID': '',
    }
    headers = {**unique_headers, **common_header}
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200 and response.json()['success']:
        # return response.text
        auth_token = response.json()['data']['activeCourseList'][0]['authToken']
        return bearer_token, auth_token
    else:
        print("Authentication failed:", response.text)
        print(response.text)


def get_slotlist(bearer_token, auth, yy, mm):
    url = utils.slotlist_url
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
      'Authorization': f'Bearer {str(bearer_token)}',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'JSESSIONID': f'Bearer {str(auth_token)}',
    }
    headers = {**unique_headers, **common_header}
    response = requests.request("POST", url, headers=headers,
                                data=json.dumps(payload))
    if response.status_code == 200 and response.json()['success']:
        new_data = response.json()['data']
        return new_data
    else:
        print(f"Error at get_slotlist {response.text}")
        print(response.text)
        return f"Error at get_slotlist {response.text}"


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
    weekends = utils.get_weekends(year, month)
    mask = df['lista'].isin(weekends) & df['slotRefName'] != 'SESSION 1'
    wkends = df[mask]
    # print(wkdays7)
    my_choice = pd.concat([wkdays7, wkends], ignore_index=True)
    # print(my_choice)
    chosen = my_choice[["slotId", "slotIdEnc", "bookingProgressEnc"]]
    # print(chosen)
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
    url = utils.submit_url
    auth_token = auth[7:]
    unique_headers = {
      'Authorization': f'Bearer {str(bearer_token)}',
      'Cookie': f'bbdc-token=Bearer%20{str(bearer_token)}',
      'JSESSIONID': f'Bearer {str(auth_token)}',
    }
    headers = {**unique_headers, **common_header}
    response = requests.request("POST", url, headers=headers,
                                data=json.dumps(payload))

    if response.status_code == 200 and response.json()['success']:
        return "success", response.json()['data']
    else:
        return "failed", None


def extract(minutes=19):
    token = login()
    # print(token)
    bearer_token, auth_token = get_jsessionid(token)
    # print(auth_token)
    month = utils.month
    year = utils.year
    weekends = utils.get_weekends(year, month)
    # count = 0
    # while True:
    t_end = time.time() + 60 * minutes
    balance_ = ""
    while time.time() < t_end:
        # print(count)
        # count += 1
        try:
            new_data = get_slotlist(bearer_token, auth_token, year, str(month).zfill(2))
            balance_ = new_data['accountBal']
            # print(new_data)
            if new_data['releasedSlotListGroupByDay'] is not None:
                check = next(iter(new_data['releasedSlotListGroupByDay'].values()))[0]
                check_val = check['slotRefName']
                check_date = check['slotRefDate']
                if check_val == "SESSION 7" or check_date in weekends:
                    chosen, balance, df = get_mychoice(new_data, year, month)
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
