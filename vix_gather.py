import argparse
import csv
import json
import sys
import time
from datetime import datetime, timedelta

import requests


def get_cookies() -> dict:
    """Retrieves a cookie from vixcentral.com

    Returns:
      A dictionary of the cookies
    """
    response = requests.get("http://vixcentral.com")

    if response.status_code == 200:
        return response.cookies.get_dict()
    else:
        return None


def get_day_data(day: str, cookies: dict = get_cookies()) -> list:
    """Retrieves data for a specific day.

    Args:
      day: "%Y-%m-%d" (YYYY-MM-DD) format of the day to pull data from
      cookies: dict of cookies for site from get_cookies function

    Returns:
      list of data for that day
    """

    timestamp = int(datetime.now().timestamp() * 1000)
    data = requests.get(f"http://vixcentral.com/ajax_historical?n1={day}&_={timestamp}")

    url = "http://vixcentral.com/ajax_historical"
    params = {"n1": f"{day}", "_": f"{timestamp}"}

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Host": "vixcentral.com",
        "Referer": "http://vixcentral.com/",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
    }

    data = requests.get(url, headers=headers, params=params, cookies=cookies)

    if data.text == '"hello historical"':
        print("Data protection hit, exiting")
        sys.exit()
    elif data.text == '"error"':
        data = ["error"]
    else:
        data = json.loads(data.text)
    # add the date of the data in there
    data.insert(0, day)
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Data puller from historical data from vixcentral.com")
    parser.add_argument("--start", help="Date to start gathering data from", default="2007-03-26")
    parser.add_argument(
        "--stop",
        help="Date to stop gathering data from",
        default=datetime.now().strftime("%Y-%m-%d"),
    )
    parser.add_argument("--output", help="CSV out file", default="vixcentral_data.csv")
    parser.add_argument("--progress", help="Print status ever x data pulls", default=40)
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.stop, "%Y-%m-%d")
    data = []
    timings = []
    x = 0
    cookies = get_cookies()

    while start < end:
        x += 1
        delta = end - start
        start_formatted = start.strftime('%Y-%m-%d')
        if x % args.progress == 0:
            print(f"Pulling data for {start_formatted}, {delta.days} pulls left")
        start_time = time.time()
        # don't bother triming data list. While it grows large, its not worth the slowdown of cutting data from it
        data.append(get_day_data(start_formatted, cookies))

        # calculate some timing things
        end_time = time.time()
        duration = end_time - start_time
        timings.append(duration)
        if x % args.progress == 0:
            average_time = sum(timings[(args.progress*-1):]) / args.progress
            time_till_done = average_time * delta.days
            end_time = datetime.now() + timedelta(seconds=time_till_done)
            print(
                f"  Average time for the last {args.progress} runs: {average_time:.4f} seconds. Estimated completion time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        start = start + timedelta(days=1)
        while start.weekday() >= 5:  # skip weekends
            start = start + timedelta(days=1)

    print(f"Writing output to: {args.output}")
    with open(args.output, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerows(data)
    print("Finished.")
