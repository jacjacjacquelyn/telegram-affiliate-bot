def generate_short_link(url: str):
    if not APP_ID or not APP_SECRET:
        print("Missing APP_ID or APP_SECRET")
        return None

    timestamp = str(int(time.time()))

    QUERY = """mutation generateShortLink($input: ShortLinkInput!){generateShortLink(input:$input){shortLink}}"""

    payload = {
        "query": QUERY,
        "operationName": "generateShortLink",
        "variables": {
            "input": {
                "originUrl": url
            }
        }
    }

    payload_str = json.dumps(payload, separators=(',', ':'))

    signature = generate_signature(APP_ID, timestamp, payload_str, APP_SECRET)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={signature}"
    }

    r = requests.post(
        GRAPHQL_URL,
        data=payload_str,
        headers=headers,
        timeout=10
    )

    print("STATUS:", r.status_code)
    print("RAW RESPONSE:", r.text)

    try:
        data = r.json()

        if "errors" in data:
            print("SHOPEE ERROR:", data["errors"])
            return None

        return data["data"]["generateShortLink"]["shortLink"]

    except Exception as e:
        print("PARSE ERROR:", e)
        return None
