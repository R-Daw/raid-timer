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
    days_until_next_monday = 7 - now.weekday()
    next_monday = now.date() + timedelta(days=days_until_next_monday)
    return next_monday + timedelta(days=weekday_index)


def create_event(channel_id, leader_id, title, description, event_date, time, duration, template_id="10"):
    hour, minute = map(int, start_time.split(":"))
    event_dt = datetime(
        event_date.year, event_date.month, event_date.day,
        hour, minute, tzinfo=PACIFIC,
    )
    date_ts = str(int(event_dt.timestamp()))
    payload = {
        "leaderId": leader_id,
        "title": title,
        "description": description,
        "date": date_ts,
        "time": time,
        "templateId": template_id,
        "advancedSettings": {
            "duration": duration 
        }
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
            "time": os.environ["WED_TIME"],
            "duration": os.environ["WED_DURATION"],
            "ping_role_ids": os.environ.get("PING_ROLE_IDS", ""),
            "template_id": "10",
        },
        {
            "name": "Saturday",
            "weekday": WEEKDAYS["saturday"],
            "channel_id": os.environ["SAT_CHANNEL_ID"],
            "leader_id": os.environ["SAT_LEADER_ID"],
            "title": os.environ.get("SAT_TITLE", "Saturday Raid"),
            "description": os.environ.get("SAT_DESCRIPTION", ""),
            "time": os.environ["SAT_TIME"],
            "duration": os.environ["SAT_DURATION"],
            "ping_role_ids": os.environ.get("PING_ROLE_IDS", ""),
            "template_id": "10",
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
                event_date, event["time"], event["duration"],
                event["template_id"]
            )
            print(f"[OK] {event['name']} event created for {event_date.isoformat()}")
        except requests.HTTPError as e:
            print(f"[FAIL] {event['name']}: {e.response.status_code} {e.response.text}")
            failures.append(event["name"])

    if failures:
        raise SystemExit(f"Failed to create: {', '.join(failures)}")


if __name__ == "__main__":
    main()
