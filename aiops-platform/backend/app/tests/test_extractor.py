from app.core.extractor import fetch_failed_logs

logs = fetch_failed_logs(10)

print("Total logs:", len(logs))

for l in logs:
    print("------------")
    print("API:", l.get("event", {}).get("api"))
    print("ERROR:", l.get("error", {}).get("message"))