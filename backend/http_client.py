"""Small JSON HTTP helper using Python's standard library."""
import json
from urllib.request import Request, urlopen


def post_json(url, payload, timeout=60):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=raw, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)
