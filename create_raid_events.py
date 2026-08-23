import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PACIFIC = ZoneInfo("America/Los_Angeles")
SERVER_ID = os.environ["RAID_SERVER_ID"]
API_KEY = os.environ["RAID_HELPER_API_KEY"]
BASE_URL = f"https://raid-helper.xyz/api/v4/servers/{SERVER_ID}/channels"

WEEKDAYS = {"wednesday": 2, "saturday": 5}


def next_weekday_date(weekday_index, now):
    days_ahead = (weekday_index - now.weekday()) % 7
    return now.date() + timedelta(days=days_ahead)


def create_event(channel_id, leader_id, title, description, event_date, time_range):
    noon = datetime(
        event_date.year, event_date.month, event_date.day,
        12, 0, tzinfo=PACIFIC,
    )
    date_ts = str(int(noon.timestamp()))
    payload = {
        "leaderId": leader_id,
        "title": title,
        "description": description,
        "date": date_ts,
        "time": time_range,
    }
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }
    url = f"{BASE_URL}/{channel_id}/event"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def main():
    now = datetime.now(PACIFIC)

    events = [
        {
            "name": "Wednesday",
            "weekday": WEEKDAYS["wednesday"],
            "channel_id": os.environ["WED_CHANNEL_ID"],
            "leader_id": os.environ["WED_LEADER_ID"],
            "title": os.environ.get("WED_TITLE", "Wednesday Raid"),
            "description": os.environ.get("WED_DESCRIPTION", ""),
            "time_range": os.environ["WED_TIME_RANGE"],
            "ping_role_ids": os.environ.get("PING_ROLE_IDS", ""),
        },
        {
            "name": "Saturday",
            "weekday": WEEKDAYS["saturday"],
            "channel_id": os.environ["SAT_CHANNEL_ID"],
            "leader_id": os.environ["SAT_LEADER_ID"],
            "title": os.environ.get("SAT_TITLE", "Saturday Raid"),
            "description": os.environ.get("SAT_DESCRIPTION", ""),
            "time_range": os.environ["SAT_TIME_RANGE"],
            "ping_role_ids": os.environ.get("PING_ROLE_IDS", ""),
        },
    ]

    failures = []
    for event in events:
        event_date = next_weekday_date(event["weekday"], now)
        description = event["description"]
        role_ids = [r.strip() for r in event["ping_role_ids"].split(",") if r.strip()]
        if role_ids:
            mentions = " ".join(f"<@&{role_id}>" for role_id in role_ids)
            description = f"{mentions} {description}".strip()
        try:
            create_event(
                event["channel_id"], event["leader_id"],
                event["title"], description,
                event_date, event["time_range"],
            )
            print(f"[OK] {event['name']} event created for {event_date.isoformat()}")
        except requests.HTTPError as e:
            print(f"[FAIL] {event['name']}: {e.response.status_code} {e.response.text}")
            failures.append(event["name"])

    if failures:
        raise SystemExit(f"Failed to create: {', '.join(failures)}")


if __name__ == "__main__":
    main()
