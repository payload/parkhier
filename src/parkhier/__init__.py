import bs4
import os
from urllib.parse import urljoin

DRESDEN_DE = "https://www.dresden.de/apps_ext/ParkplatzApp/index"
HTTP_CACHE_USE = True
CACHE_DIR = ".cache"


def fetch_parking_spaces(end=None):
    text = http_get(DRESDEN_DE)
    soup = bs4.BeautifulSoup(text, "html.parser")
    tables = soup.select(".article_content table")
    spaces = (extract_parking_space_from_html_table(table) for table in tables)
    spaces = [space for space_group in spaces for space in space_group]
    spaces = spaces if not end else spaces[:end]
    for space in spaces:
        space["details"] = fetch_parking_space_details(space)
    return spaces


def http_get(url: str):
    # if file exists in cache/sha1 return file content
    # if not fetch from url and save to cache/sha1
    import hashlib

    hash = hashlib.sha1(url.encode()).hexdigest()
    if HTTP_CACHE_USE and not cache_outdated():
        text = read_cache(hash)
        if text:
            return text
    import httpx

    response = httpx.get(url)
    if HTTP_CACHE_USE:
        write_cache(hash, response.text)
    return response.text


def read_cache(filename: str) -> str | None:
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        with open(filepath, "r") as f:
            return f.read()
    except Exception:
        return None


def write_cache(filename: str, text: str):
    filepath = os.path.join(CACHE_DIR, filename)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(filepath, "w+") as f:
        f.write(text)


def cache_timestamp():
    try:
        return float(read_cache("timestamp"))
    except Exception:
        return 0.0


def cache_outdated():
    import time

    timestamp = read_cache("timestamp")
    if timestamp and time.monotonic() - float(timestamp) < 60:
        return False
    write_cache("timestamp", str(time.monotonic()))
    return True


def fetch_parking_space_details(space: dict):
    text = http_get(space["detail_url"])
    soup = bs4.BeautifulSoup(text, "html.parser")

    tendency = extract_label_value_from_html_divs(soup, "Tendenz:")
    last_update = extract_label_value_from_html_divs(soup, "Letzte Aktualisierung:")
    gps_lon = extract_label_value_from_html_divs(soup, "GPS-Lon:")
    gps_lat = extract_label_value_from_html_divs(soup, "GPS-Lat:")
    image_url = urljoin(DRESDEN_DE, soup.select_one('img[alt="image"]')["src"])
    # TODO gps coordinates are completely off on dresden.de details page
    #      need to enter or find correct gps coordinates, need to double check

    return {
        "tendency": tendency,
        "last_update": last_update,
        "gps_lon": gps_lon,
        "gps_lat": gps_lat,
        "image_url": image_url,
    }


def extract_label_value_from_html_divs(soup: bs4.BeautifulSoup, label: str):
    label_divs = [div for div in soup.select("div") if div.text == label]
    if len(label_divs) > 1:
        print("expected only one div with label", label)
    if len(label_divs) == 0:
        return ""
    label_div = label_divs[0]
    next_div = label_div.find_next("div")
    return next_div.text.strip() if next_div else ""


def extract_parking_space_from_html_table(table: bs4.Tag):
    head = table.select("thead th")
    rows = [row.select("td") for row in table.select("tbody tr")]

    if len(head) != 4:
        print("expected table head with 4 elements", len(head), head)
    for row in rows:
        if len(row) != 4:
            print("expected table rows with 4 elements", len(row), row)

    category = head[1].text.strip()
    return [
        {
            "category": category,
            "indicator": extract_indicator_td(row[0]),
            "location": row[1].select_one(".content").text.strip(),
            "detail_url": urljoin(DRESDEN_DE, row[1].select_one("a")["href"]),
            "spaces": row[2].select_one(".content").text.strip(),
            "free": row[3].select_one(".content").text.strip(),
        }
        for row in rows
    ]


def extract_indicator_td(td: bs4.Tag):
    classes = td["class"]
    known = ["park-logo", "park-closed", "red", "yellow", "green", "blue"]
    return " ".join(x for x in known if x in classes)


def main_fetch():
    import json
    print(json.dumps(fetch_parking_spaces(end=3), indent=2))
