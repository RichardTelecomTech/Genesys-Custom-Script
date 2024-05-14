import requests
import json
from datetime import datetime, timedelta
import calendar
import os

# Define the URL for the API endpoint
url = 'https://api.mypurecloud.com.au/api/v2/analytics/conversations/aggregates/query'

# Define the headers including the access token
headers = {
    'Authorization': 'Bearer ENTER_ACCESS_TOKEN',
    'Content-Type': 'application/json'
}

# Function to get the start and end dates for each month in the interval
def get_monthly_intervals(start_date, end_date):
    current_date = start_date
    intervals = []

    while current_date < end_date:
        first_day = current_date.replace(day=1)
        last_day = current_date.replace(day=calendar.monthrange(current_date.year, current_date.month)[1])
        if last_day > end_date:
            last_day = end_date

        intervals.append((first_day, last_day))
        current_date = first_day + timedelta(days=calendar.monthrange(current_date.year, current_date.month)[1])

    return intervals

# Define the start and end dates
start_date = datetime.strptime("2023-03-31T13:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
end_date = datetime.strptime("2024-05-14T14:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")

# Get the monthly intervals
monthly_intervals = get_monthly_intervals(start_date, end_date)

# Function to make the API request for a given interval
def make_api_request(start, end):
    body = {
      "interval": f"{start.isoformat()}Z/{end.isoformat()}Z",
      "groupBy": [
        "originatingDirection",
        "queueId"
      ],
      "filter": {
        "type": "and",
        "clauses": [
          {
            "type": "or",
            "predicates": [
              {
                "type": "dimension",
                "dimension": "queueId",
                "operator": "matches",
                "value": "963d7505-d432-4d8e-a795-7c8d32d71d32"
              },
              {
                "type": "dimension",
                "dimension": "queueId",
                "operator": "matches",
                "value": "f673f628-82d8-4821-ae8d-5cce32e11354"
              },
              {
                "type": "dimension",
                "dimension": "queueId",
                "operator": "matches",
                "value": "baf3bf54-508a-41d5-b97d-f34dfe840a1b"
              },
              {
                "type": "dimension",
                "dimension": "queueId",
                "operator": "matches",
                "value": "6cac567d-9686-45b3-9d9a-f86244493657"
              },
              {
                "type": "dimension",
                "dimension": "queueId",
                "operator": "matches",
                "value": "b944adb0-5bb1-4aac-8e25-f86fcdd968b1"
              }
            ]
          }
        ],
        "predicates": [
          {
            "type": "dimension",
            "dimension": "originatingDirection",
            "operator": "matches",
            "value": "inbound"
          },
          {
            "type": "dimension",
            "dimension": "mediaType",
            "operator": "matches",
            "value": "voice"
          }
        ]
      },
      "views": [],
      "metrics": [
        "nOffered",
        "tAnswered"
      ],
      "timeZone": "Australia/Sydney",
      "granularity": "PT30M"
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed for interval {start} to {end} with status code: {response.status_code}")
        print(response.json())
        return None

# Collect all results
all_results = {
    "interval": f"{start_date.isoformat()}Z/{end_date.isoformat()}Z",
    "data": []
}

for start, end in monthly_intervals:
    result = make_api_request(start, end)
    if result:
        all_results["data"].extend(result["results"])

# Output the collected results as a single JSON to the specified path
output_path = r"C:\Genesys Cloud\Analytics\combined_results.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"Results saved to {output_path}")
