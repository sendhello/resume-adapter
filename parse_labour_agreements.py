#!/usr/bin/env python3
"""
Parse the list of current labour agreements from the Australian Department of Home Affairs
via the SharePoint API and save it to a CSV file.
"""

import csv
import json
import sys
import time
import requests

BASE_URL = "https://immi.homeaffairs.gov.au"
API_URL = f"{BASE_URL}/_layouts/15/api/Data.aspx/GetLabourAgreementData"
API_PAYLOAD = {"webUrl": "/employer-subsite", "category": "All"}

OUTPUT_FILE = "labour_agreements.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json; charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": (
        f"{BASE_URL}/visas/employing-and-sponsoring-someone/"
        "labour-agreements/list-of-current-labour-agreements"
    ),
}


def fetch_data() -> list[dict]:
    session = requests.Session()

    # Get cookies from the main page first
    print("Getting session cookies...")
    session.get(BASE_URL, headers={**HEADERS, "Accept": "text/html"}, timeout=30)
    time.sleep(1)

    print(f"Fetching data from API: {API_URL}")
    response = session.post(
        API_URL,
        json=API_PAYLOAD,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    # The API may wrap results in a "d" key (SharePoint REST convention)
    if isinstance(data, dict):
        if "d" in data:
            data = data["d"]
        # May be further nested
        if isinstance(data, dict):
            # Try common keys
            for key in ("results", "data", "items", "rows"):
                if key in data:
                    data = data[key]
                    break

    if not isinstance(data, list):
        print(f"Unexpected response format: {type(data)}", file=sys.stderr)
        print(json.dumps(data, indent=2)[:1000], file=sys.stderr)
        sys.exit(1)

    return data


def save_csv(records: list[dict], output_file: str) -> None:
    if not records:
        print("No records to save.")
        return

    # Use the keys from the first record as column headers,
    # but map to human-readable names based on the page config
    field_map = {
        "companyname": "Company name",
        "latype": "LA type",
        "startdate": "Start date",
        "enddate": "End date",
    }

    # Collect all keys present in data
    all_keys = list(records[0].keys())
    headers = [field_map.get(k, k) for k in all_keys]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for record in records:
            writer.writerow([record.get(k, "") for k in all_keys])

    print(f"Saved {len(records)} records to {output_file}")


def main():
    records = fetch_data()
    print(f"Received {len(records)} records.")
    save_csv(records, OUTPUT_FILE)


if __name__ == "__main__":
    main()