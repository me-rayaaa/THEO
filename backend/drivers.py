import requests

url = "https://api.openf1.org/v1/drivers?session_key=9877"

response = requests.get(url)
data = response.json()

for driver in data:
    print(
        driver["driver_number"],
        "-",
        driver["full_name"],
        "-",
        driver["team_name"]
    )