import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os
from urllib.parse import urljoin

URL = "https://lifelineanimal.org/adopt/?Species_1=Cat&Sex_1=Female&Age_1=%3C6&Age_2=6-12"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

ALLOWED_LOCATIONS = [
    "LifeLine Community Animal Center",
    "Fulton County Animal Services",
    "DeKalb County Animal Services"
]


def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split()).strip()


def extract_age(text):
    text_lower = text.lower()

    age_keywords = [
        "week", "weeks",
        "month", "months",
        "year", "years",
        "baby", "young"
    ]

    lines = [clean_text(line) for line in text.split("\n")]
    lines = [line for line in lines if line]

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in age_keywords):
            return line

    return "Age not listed"


def extract_location(text):
    for location in ALLOWED_LOCATIONS:
        if location in text:
            return location
    return "Location not listed"


def extract_image(card):
    img = card.select_one("img")
    if not img:
        return ""

    possible_attrs = ["src", "data-src", "data-lazy-src", "data-original"]

    for attr in possible_attrs:
        value = img.get(attr)
        if value and value.strip():
            return urljoin("https://lifelineanimal.org", value.strip())

    return ""


def get_cats():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cats = []

    cards = soup.select(".grid-item")

    for card in cards:
        link_tag = card.select_one("a")
        name_tag = card.select_one(".field--name-title")

        if not link_tag or not name_tag:
            continue

        raw_text = clean_text(card.get_text(" ", strip=True))
        location = extract_location(raw_text)

        if location not in ALLOWED_LOCATIONS:
            continue

        name = clean_text(name_tag.get_text())
        detail_url = urljoin("https://lifelineanimal.org", link_tag.get("href", ""))
        age = extract_age(card.get_text("\n", strip=True))
        image_url = extract_image(card)

        cat_id = detail_url if detail_url else name

        cats.append({
            "id": cat_id,
            "name": name,
            "age": age,
            "location": location,
            "url": detail_url,
            "image_url": image_url
        })

    return cats


def load_seen():
    if os.path.exists("seen.json"):
        with open("seen.json", "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_seen(ids):
    with open("seen.json", "w", encoding="utf-8") as f:
        json.dump(ids, f, ensure_ascii=False, indent=2)


def build_html_email(new_cats):
    html = """
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.5;">
        <h2>New cats found 🐱</h2>
    """

    for cat in new_cats:
        name = cat.get("name", "Unknown")
        age = cat.get("age", "Age not listed")
        location = cat.get("location", "Location not listed")
        url = cat.get("url", "")
        image_url = cat.get("image_url", "")

        html += f"""
        <div style="margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #ddd;">
          <h3 style="margin-bottom: 8px;">{name}</h3>
          <p style="margin: 4px 0;"><strong>Age:</strong> {age}</p>
          <p style="margin: 4px 0;"><strong>Location:</strong> {location}</p>
        """

        if image_url:
            html += f"""
            <p style="margin: 12px 0;">
              <img src="{image_url}" alt="{name}" style="max-width: 240px; height: auto; border-radius: 8px;">
            </p>
            """

        if url:
            html += f"""
            <p style="margin: 8px 0;">
              <a href="{url}" target="_blank">View details</a>
            </p>
            """

        html += "</div>"

    html += """
      </body>
    </html>
    """

    return html


def build_text_email(new_cats):
    body = "New cats found:\n\n"

    for cat in new_cats:
        body += f"Name: {cat.get('name', 'Unknown')}\n"
        body += f"Age: {cat.get('age', 'Age not listed')}\n"
        body += f"Location: {cat.get('location', 'Location not listed')}\n"
        body += f"Link: {cat.get('url', '')}\n"
        body += "\n"

    return body


def send_email(new_cats):
    email_user = os.environ["EMAIL_USER"]
    email_pass = os.environ["EMAIL_PASS"]
    to_email = os.environ["TO_EMAIL"]

    text_body = build_text_email(new_cats)
    html_body = build_html_email(new_cats)

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = "New kittens available 🐱"
    msg["From"] = email_user
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_user, email_pass)
        server.sendmail(email_user, [to_email], msg.as_string())


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


if __name__ == "__main__":
    main()
