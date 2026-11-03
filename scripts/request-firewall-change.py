#!/usr/bin/env python3
"""Submit a Firewall Rule Change service request in ServiceNow.

Orders the catalog item created by setup-firewall-catalog.py and prints
the resulting REQ/RITM details for the ServiceNow side of the demo.

Usage:
    python3 scripts/request-firewall-change.py
    python3 scripts/request-firewall-change.py \\
      --source-network 10.10.20.0/24 \\
      --destination-network 10.50.1.0/24 \\
      --destination-port 443 \\
      --protocol tcp \\
      --action allow

Reads SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD
from the environment or the repo-root .env file.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ITEM_NAME = "Firewall Rule Change"


def load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        # Prefer .env over empty/stale shell exports so auth does not fail with 401.
        os.environ[key.strip()] = value.strip().strip("'\"")


def env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


class Snow:
    def __init__(self, instance: str, username: str, password: str) -> None:
        self.base = instance.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.ctx = ssl.create_default_context()

    def request(self, method: str, path: str, body: dict | None = None, query: dict | None = None):
        url = self.base + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, context=self.ctx) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise SystemExit(f"{method} {path} failed ({exc.code}): {detail[:500]}") from exc

    def first(self, table: str, query: str, fields: str = "sys_id,name") -> dict | None:
        result = self.request(
            "GET",
            f"/api/now/table/{table}",
            query={
                "sysparm_query": query,
                "sysparm_fields": fields,
                "sysparm_limit": "1",
            },
        )
        rows = result.get("result") or []
        return rows[0] if rows else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Request a firewall rule change via Service Catalog.")
    parser.add_argument("--source-network", default="10.10.20.0/24")
    parser.add_argument("--destination-network", default="10.50.1.0/24")
    parser.add_argument("--destination-port", default="443")
    parser.add_argument("--protocol", default="tcp", choices=["tcp", "udp", "icmp"])
    parser.add_argument("--action", default="allow", choices=["allow", "deny"])
    parser.add_argument(
        "--direction",
        default="bidirectional",
        choices=["inbound", "outbound", "bidirectional"],
    )
    parser.add_argument(
        "--justification",
        default="Allow app tier to reach payments API over HTTPS for release cutover.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(repo_root / ".env")
    instance = env("SERVICENOW_INSTANCE_URL", "SN_INSTANCE")
    username = env("SERVICENOW_USERNAME", "SN_USERNAME")
    password = env("SERVICENOW_PASSWORD", "SN_PASSWORD")
    if not (instance and username and password):
        raise SystemExit(
            "Set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD in .env"
        )

    snow = Snow(instance, username, password)
    item = snow.first("sc_cat_item", f"name={ITEM_NAME}^active=true", "sys_id,name")
    if item is None:
        raise SystemExit(
            f"Catalog item '{ITEM_NAME}' not found. Run: python3 scripts/setup-firewall-catalog.py"
        )

    variables = {
        "source_network": args.source_network,
        "destination_network": args.destination_network,
        "destination_port": str(args.destination_port),
        "protocol": args.protocol,
        "action": args.action,
        "direction": args.direction,
        "justification": args.justification,
    }

    result = snow.request(
        "POST",
        f"/api/sn_sc/servicecatalog/items/{item['sys_id']}/order_now",
        {
            "sysparm_quantity": "1",
            "variables": variables,
        },
    )
    request = result.get("result") or {}
    request_number = request.get("request_number") or request.get("number") or ""
    request_id = request.get("sys_id") or request.get("request_id") or ""

    ritm = None
    for _ in range(10):
        if request_id:
            ritm = snow.first(
                "sc_req_item",
                f"request={request_id}",
                "sys_id,number,short_description",
            )
        if ritm:
            break
        time.sleep(1)

    ritm_number = (ritm or {}).get("number") or ""
    ritm_sys_id = (ritm or {}).get("sys_id") or ""
    short_description = (ritm or {}).get("short_description") or ""

    print(f"Created request {request_number}")
    if ritm_number:
        print(f"Created RITM {ritm_number}")
        print(f"Short description: {short_description}")
        print(f"URL: {snow.base}/nav_to.do?uri=sc_req_item.do?sys_id={ritm_sys_id}")
    print()
    print("Rule details (for the Manage Firewall Rules job survey):")
    print(f"  Source network:       {args.source_network}")
    print(f"  Destination network:  {args.destination_network}")
    print(f"  Destination port:     {args.destination_port}")
    print(f"  Protocol:             {args.protocol}")
    print(f"  Action:               {args.action}")
    print(f"  Direction:            {args.direction}")
    print(f"  Justification:        {args.justification}")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
