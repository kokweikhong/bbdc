import json
import requests


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


def get_jsessionid(bearer_token):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/account/listAccountCourseType"
    headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {str(bearer_token)}",
                "Content-Type": "application/json"
              }
    # payload = {}
    #
    #     "Cookie": f"bbdc-token=Bearer%20{str(bearer_token)}",
    # "JSESSIONID": ""
    resp = requests.post(url, headers=headers, data="{}")
    if resp.status_code == 200:
        return resp.text
        # auth_token = resp.json()["data"]["activeCourseList"]["authToken"]
        # return auth_token
    else:
        print("Authentication failed:", resp.text)


def get_table(bearer_token, auth_token):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c3practical/listC3PracticalSlotReleased"
    headers = {
        "Authorization": f"Bearer {str(bearer_token)}",
        "Content-Type": "application/json"
    }
    payload = '{\
            "courseType": "3A",\
            "insInstructorId": "",\
            "releasedSlotMonth": "202308",\
            "stageSubDesc": "Practical Lesson",\
            "subVehicleType": Null,\
            "subStageSubNo": Null\
           }'

    resp = requests.post(url, headers=headers, data=json.loads(payload))

    if resp.status_code != 200:
        print('error: ' + str(resp.status_code))
    else:
        print('List Loaded Successfully')
        print(resp.text)


if __name__ == '__main__':
    bearer_token = login()
    print(bearer_token)
    auth_token = get_jsessionid(bearer_token)
    print(auth_token)
    # get_table(bearer_token)
