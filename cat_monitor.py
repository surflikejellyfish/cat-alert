import requests
import json
import smtplib
from email.mime.text import MIMEText
import os

URL = "https://toolkit.rescuegroups.org/of/f?c=97&species=cat&sex=female&age=Baby,Young"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def get_cats():
    response = requests.get(URL, headers=HEADERS)
    data = response.json()
    
    cats = []
    for animal in data["data"]:
        name = animal["name"]
        age = animal["ageGroup"]
        location = animal["locationName"]
        url = animal["url"]

        if location in [
            "LifeLine Community Animal Center",
            "Fulton County Animal Services",
            "DeKalb County Animal Services"
        ]:
            cats.append({
                "id": animal["id"],
                "name": name,
                "age": age,
                "location": location,
                "url": url
            })
    return cats


def load_seen():
    if os.path.exists("seen.json"):
        with open("seen.json", "r") as f:
            return json.load(f)
    return []


def save_seen(ids):
    with open("seen.json", "w") as f:
        json.dump(ids, f)


def send_email(new_cats):
    EMAIL = os.environ["EMAIL_USER"]
    PASSWORD = os.environ["EMAIL_PASS"]
    TO = os.environ["TO_EMAIL"]

    body = "New cats found:\n\n"
    for cat in new_cats:
        body += f"{cat['name']} | {cat['age']} | {cat['location']}\n{cat['url']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = "🐱 New kittens available!"
    msg["From"] = EMAIL
    msg["To"] = TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)


def main():
    cats = get_cats()
    seen = load_seen()

    new_cats = [c for c in cats if c["id"] not in seen]

    if new_cats:
        send_email(new_cats)

    save_seen([c["id"] for c in cats])


if __name__ == "__main__":
    main()
