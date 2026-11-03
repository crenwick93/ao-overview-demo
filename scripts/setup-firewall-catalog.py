#!/usr/bin/env python3
"""Create the ServiceNow catalog item for firewall rule change requests.

Item: "Firewall Rule Change"
Category: Network (under Service Catalog)

Form variables align with the Manage Firewall Rules job survey fields
(source/destination/port/protocol/action/direction/justification):
  source_network, destination_network, destination_port, protocol,
  action, direction, justification

Usage:
    python3 scripts/setup-firewall-catalog.py

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
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ITEM_NAME = "Firewall Rule Change"
CATEGORY_TITLE = "Network"
RULE_NAME = "AO Overview Demo — Firewall Rule Change short description"

VARIABLES = [
    {
        "name": "source_network",
        "question_text": "Source network (CIDR)",
        "type": "6",
        "mandatory": "true",
        "order": "100",
        "default_value": "10.10.20.0/24",
    },
    {
        "name": "destination_network",
        "question_text": "Destination network (CIDR)",
        "type": "6",
        "mandatory": "true",
        "order": "200",
        "default_value": "10.50.1.0/24",
    },
    {
        "name": "destination_port",
        "question_text": "Destination port",
        "type": "6",
        "mandatory": "true",
        "order": "300",
        "default_value": "443",
    },
    {
        "name": "protocol",
        "question_text": "Protocol",
        "type": "5",
        "mandatory": "true",
        "order": "400",
        "default_value": "tcp",
        "choices": [("TCP", "tcp"), ("UDP", "udp"), ("ICMP", "icmp")],
    },
    {
        "name": "action",
        "question_text": "Action",
        "type": "5",
        "mandatory": "true",
        "order": "500",
        "default_value": "allow",
        "choices": [("Allow", "allow"), ("Deny", "deny")],
    },
    {
        "name": "direction",
        "question_text": "Direction",
        "type": "5",
        "mandatory": "true",
        "order": "600",
        "default_value": "bidirectional",
        "choices": [
            ("Inbound", "inbound"),
            ("Outbound", "outbound"),
            ("Bidirectional", "bidirectional"),
        ],
    },
    {
        "name": "justification",
        "question_text": "Business justification",
        "type": "2",
        "mandatory": "true",
        "order": "700",
        "default_value": "Allow app tier to reach payments API over HTTPS for release cutover.",
    },
]


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

    def ensure(self, table: str, query: str, data: dict) -> tuple[str, bool]:
        existing = self.first(table, query)
        if existing:
            return existing["sys_id"], False
        created = self.request("POST", f"/api/now/table/{table}", data)
        return created["result"]["sys_id"], True


def rule_script() -> str:
    return """(function executeRule(current, previous) {
    var source = (current.variables.source_network || '') + '';
    var destination = (current.variables.destination_network || '') + '';
    var port = (current.variables.destination_port || '') + '';
    var protocol = (current.variables.protocol || 'tcp') + '';
    var action = (current.variables.action || 'allow') + '';
    if (source && destination) {
        current.short_description = 'Firewall Rule Change: ' + action.toUpperCase()
            + ' ' + source + ' -> ' + destination + ' ' + protocol.toUpperCase() + '/' + port;
    }
})(current, previous);
"""


def setup(snow: Snow) -> str:
    catalog = snow.first("sc_catalog", "title=Service Catalog^active=true", "sys_id,title")
    if catalog is None:
        catalog = snow.first("sc_catalog", "active=true", "sys_id,title")
    if catalog is None:
        raise SystemExit("No active Service Catalog found on this instance.")

    category_id, category_created = snow.ensure(
        "sc_category",
        f"title={CATEGORY_TITLE}^sc_catalog={catalog['sys_id']}",
        {
            "title": CATEGORY_TITLE,
            "description": "Network connectivity and firewall change requests.",
            "sc_catalog": catalog["sys_id"],
            "active": "true",
        },
    )
    print(f"{'created' if category_created else 'found'} category {CATEGORY_TITLE}")

    item_id, item_created = snow.ensure(
        "sc_cat_item",
        f"name={ITEM_NAME}",
        {
            "name": ITEM_NAME,
            "short_description": "Request a firewall rule change between two networks",
            "description": (
                "Submit a request to allow or deny traffic between a source and "
                "destination network. A network engineer will fulfil this using "
                "the Manage Firewall Rules job in Ansible Automation Platform."
            ),
            "active": "true",
            "state": "published",
            "availability": "on_desktop",
            "no_quantity": "true",
            "omit_price": "true",
        },
    )
    print(f"{'created' if item_created else 'found'} catalog item {ITEM_NAME} ({item_id})")

    _, link_created = snow.ensure(
        "sc_cat_item_category",
        f"sc_cat_item={item_id}^sc_category={category_id}",
        {"sc_cat_item": item_id, "sc_category": category_id},
    )
    print(f"{'linked' if link_created else 'already linked'} item to {CATEGORY_TITLE}")

    for variable in VARIABLES:
        variable_id, variable_created = snow.ensure(
            "item_option_new",
            f"cat_item={item_id}^name={variable['name']}",
            {
                "cat_item": item_id,
                "name": variable["name"],
                "question_text": variable["question_text"],
                "type": variable["type"],
                "mandatory": variable["mandatory"],
                "order": variable["order"],
                "default_value": variable.get("default_value", ""),
                "active": "true",
            },
        )
        print(f"{'created' if variable_created else 'found'} variable {variable['name']}")
        for index, (label, value) in enumerate(variable.get("choices", []), start=1):
            _, choice_created = snow.ensure(
                "question_choice",
                f"question={variable_id}^value={value}",
                {
                    "question": variable_id,
                    "text": label,
                    "value": value,
                    "order": str(index * 100),
                    "inactive": "false",
                },
            )
            print(f"{'created' if choice_created else 'found'} choice {variable['name']}={value}")

    _, rule_created = snow.ensure(
        "sys_script",
        f"name={RULE_NAME}",
        {
            "name": RULE_NAME,
            "collection": "sc_req_item",
            "when": "before",
            "advanced": "true",
            "action_insert": "true",
            "active": "true",
            "order": "100",
            "filter_condition": f"cat_item={item_id}",
            "script": rule_script(),
        },
    )
    print(f"{'created' if rule_created else 'found'} business rule")
    print(f"Catalog item URL: {snow.base}/sp?id=sc_cat_item&sys_id={item_id}")
    print(f"Item sys_id: {item_id}")
    return item_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the Firewall Rule Change catalog item.")
    parser.parse_args()

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
    setup(snow)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
