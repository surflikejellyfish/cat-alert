import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os

URL = "https://lifelineanimal.org/adopt/?Species_1=Cat&Sex_1=Female&Age_1=%3C6&Age_2=6-12"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_cats():
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    cats = []

    cards = soup.select(".grid-item")

    for card in cards:
        name = card.select_one(".field--name-title")
        link = card.select_one("a")

        if not name or not link:
            continue

        name = name.text.strip()
        url = "https://lifelineanimal.org" + link["href"]

        # 简单过滤 location（页面里会带）
        text = card.text

        if any(loc in text for loc in [
            "LifeLine Community Animal Center",
            "Fulton County Animal Services",
            "DeKalb County Animal Services"
        ]):
            cats.append({
                "id": url,
                "name": name,
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
        body += f"{cat['name']}\n{cat['url']}\n\n"

    msg = MIMEText(body)
    msg["Subject"] = "🐱 New kittens available!"
    msg["From"] = EMAIL
    msg["To"] = TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)


def main():
    cats = get_cats()
    print(f"Found {len(cats)} matching cats.")

    seen = load_seen()
    new_cats = [c for c in cats if c["id"] not in seen]

    print(f"Found {len(new_cats)} new cats.")

    if new_cats:
        send_email(new_cats)
        print("Email sent.")
    else:
        print("No new cats.")

    save_seen([c["id"] for c in cats])
    print("Saved seen.json.")
