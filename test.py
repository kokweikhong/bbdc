from datetime import datetime, timedelta
import calendar
import json
import pandas as pd
from time import sleep


def get_weekends(year=2023, month=8):
    # Set the year and month you want to get the weekends for
    # Get the calendar for the given month
    cal = calendar.monthcalendar(year, month)
    # Iterate over the weeks in the calendar
    weekends = [f'{year}-{month}-{day}' for week in cal for day in week[5:7] if day != 0]
    weekend_objects = [datetime.strptime(weekend,
                                         '%Y-%m-%d') for weekend in weekends]
    weekend_strings = [weekend_object.strftime('%Y-%m-%d %H:%M:%S') for weekend_object in weekend_objects]
    return weekend_strings


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
    weekends = get_weekends()
    mask = df['lista'].isin(weekends) & df['slotRefName'] != 'SESSION 1'
    wkends = df[mask]
    my_choice = pd.concat([wkdays7, wkends], ignore_index=True)
    chosen = my_choice[["slotId", "slotIdEnc", "bookingProgressEnc"]]
    return chosen, balance, df


def main():
    weekends = get_weekends()
    with open('data.json', 'r') as f:
        data = json.loads(f.read())

    new_data = data['data']
    # Get the latest slot list data
    # print(new_data)
    balance_ = new_data['accountBal']
    # Check if any slots are available
    if new_data['releasedSlotListGroupByDay'] is not None:
        while True:
            temp = next(iter(new_data['releasedSlotListGroupByDay'].values()))[0]
            # Get the first available slot
            # while True:
        # item will be "end" if iteration is complete


            print(temp)
            sleep(1)
        #     slot_name = first_slot['slotRefName']
        #     slot_date = first_slot['slotRefDate']
        # # Check if the slot is valid (on a weekend or session 7)
        #     if slot_name == "SESSION 7" or slot_date in weekends:
        #         print(first_slot)

    #         # Try to book the slot
    #         chosen_slots, balance, df = get_mychoice(new_data)
    #         for index, row in chosen_slots.iterrows():
    #             if balance < 78 or index >= len(chosen_slots):
    #                 break
    #             # # for row in chosen.itertuples():
    #             # slot_id = row['slotId'].item()
    #             # enc_slot_id = row['slotIdEnc']
    #             # enc_progress = row['bookingProgressEnc']
    #             # print(slot_id, enc_progress, enc_slot_id)
    #             # balance -= 77
    #         # print(new_data)


if __name__ == '__main__':
    # print(get_weekends())
    main()


