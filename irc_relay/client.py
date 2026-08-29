#!/usr/bin/env python3
"""Dev script for manually sending test messages to the HTTP API."""

import json
import urllib.request

from irc_relay.config.runtime import RuntimeConfig


def send_message(address: str, port: int, channel: str, message: str) -> None:
    data = json.dumps({"channel": channel, "string": message}).encode("utf-8")
    req = urllib.request.Request(
        f"http://{address}:{port}/",
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)  # nosec B310


def send_edit(address: str, port: int, payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{address}:{port}/",
        data=data,
        method="PUT",
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)  # nosec B310


def main():
    runtime_config = RuntimeConfig.from_env()
    address = runtime_config.metrics.address
    port = runtime_config.metrics.port

    send_message(
        address,
        port,
        "#wikipedia-en-cbngfeed",
        "[[Type Dangerous]]  https://en.wikipedia.org/w/index.php?diff=1314252715&oldid=1313754858 * 2603:7081:1C00:534F:2199:A1F4:BA71:639E * (+0) /* Composition and lyrics */ # 0.041757 # Below threshold # Not reverted",
    )
    send_edit(
        address,
        port,
        {
            "change": {
                "title": "Spanish–American War",
                "user": "50.216.6.66",
                "url": "https://en.wikipedia.org/w/index.php?diff=1314252669&oldid=1310871853",
                "revision_id": 1314252669,
                "namespace": "",
                "flags": [],
                "length": "-683",
                "comment": "",
            },
            "reverted": False,
            "comment": None,
            "score": 0.779827,
        },
    )


if __name__ == "__main__":
    main()
