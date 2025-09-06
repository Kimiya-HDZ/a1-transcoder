# load_test.py
import json, time, concurrent.futures, requests, pathlib

BASE = "http://127.0.0.1:8000"

def login(username="admin", password="admin123"):
    r = requests.post(f"{BASE}/auth/login",
                      headers={"Content-Type":"application/json"},
                      data=json.dumps({"username": username, "password": password}))
    r.raise_for_status()
    return r.json()["access_token"]

def upload(token, filepath: str):
    with open(filepath, "rb") as f:
        files = {"file": (pathlib.Path(filepath).name, f, "video/mp4")}
        r = requests.post(f"{BASE}/videos/upload",
                          headers={"Authorization": f"Bearer {token}"},
                          files=files)
    r.raise_for_status()
    return r.json()["video_id"]

def submit_job(token, video_id, renditions):
    r = requests.post(f"{BASE}/jobs/transcode",
                      headers={"Authorization": f"Bearer {token}",
                               "Content-Type":"application/json"},
                      data=json.dumps({"video_id": video_id, "renditions": renditions}))
    r.raise_for_status()
    return r.json()["job_id"]

def main():
    token = login()
    print("Logged in.")

    sample_path = input("Path to a local MP4 to stress (e.g. C:\\videos\\sample.mp4): ").strip('" ')
    N = int(input("How many parallel jobs? (start with 6–12): "))
    print("Uploading once so jobs reuse the same input…")
    vid = upload(token, sample_path)
    print("Uploaded video_id:", vid)

    # Heavier settings to keep CPU busy
    rendition = {"width":1920, "height":1080, "crf":18, "suffix":"1080p"}
    renditions = [rendition]  # or add more variants here

    print(f"Submitting {N} jobs…")
    with concurrent.futures.ThreadPoolExecutor(max_workers=N) as ex:
        futs = [ex.submit(submit_job, token, vid, renditions) for _ in range(N)]
        job_ids = [f.result() for f in futs]

    print("Submitted jobs:", job_ids)
    print("Now watch CPU usage (Task Manager → Performance → CPU).")
    # Optional short poll on first job so you see progress textually
    for _ in range(12):
        time.sleep(5)
        j0 = job_ids[0]
        r = requests.get(f"{BASE}/jobs/{j0}", headers={"Authorization": f"Bearer {token}"})
        try:
            print("Job", j0, "status:", r.json().get("status"))
        except Exception:
            pass

if __name__ == "__main__":
    main()
