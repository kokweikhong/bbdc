Now only for BBDC Class3A practical bookings


Edit config.json for 
1. Telegram token
2. Login Details

3. Choose wanted session timings for week days and weekends as shown

![image](https://user-images.githubusercontent.com/20748792/228787490-05d23a5f-1d62-4b5c-a4e3-749290d35246.png)

Book to start booking practical lessons.
Check to check booked lessons.

Once "Book" is sent to telegram bot, it will check for available slots based on wanted sessions defined in config.json file for 19 minutes.
Why 19 minutes? This to to emulate 20minutes auto logout in BBDC website or else will raise suspicions.

Sometimes, server is too busy and will not be able to response. 
Then it will throw error. 
Once it occurs, wait a while to try again.
If log in too many times , will be banned to log in for 24 hours. 
I encountered the ban once when I was developing this. So be careful!
