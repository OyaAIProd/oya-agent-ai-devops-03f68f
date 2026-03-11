import os, json, httpx
try:
    token = os.environ["SLACK_BOT_TOKEN"]
    inp = json.loads(os.environ.get("INPUT_JSON", "{}"))
    channel = inp.get("channel", "")
    thread_ts = inp.get("thread_ts", "")
    text = inp.get("text", "")
    if not channel or not text:
        print(json.dumps({"error": "channel and text are required"}))
    else:
        payload = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        with httpx.Client(timeout=15) as c:
            r = c.post("https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload)
            data = r.json()
        # Fallback: if thread not found, post to channel directly
        if not data.get("ok") and data.get("error") == "thread_not_found" and thread_ts:
            payload.pop("thread_ts", None)
            r = c.post("https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload)
            data = r.json()
        if data.get("ok"):
            print(json.dumps({"ok": True, "channel": channel, "ts": data.get("ts")}))
        else:
            print(json.dumps({"error": data.get("error", "unknown")}))
except Exception as e:
    print(json.dumps({"error": str(e)}))
