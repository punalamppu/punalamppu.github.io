"""Ilmoittaa sivukartan osoitteet hakukoneille IndexNow-rajapinnan kautta (Bing, Yandex, Seznam ym.).

Ajetaan julkaisun jälkeen. Tarkistaa ensin, että avaintiedosto näkyy livesivulla,
ja kirjaa virhetilanteessa palvelimen vastauksen, jotta syy näkyy Actions-lokissa.
"""
import json, os, re, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
BASE = CFG["baseUrl"].rstrip("/")
HOST = BASE.split("//", 1)[1]
KEY = "0fb8e0f8d03566e609802e230c9cc404"
KEY_URL = f"{BASE}/{KEY}.txt"
UA = CFG.get("userAgent") or "Punalamppu/1.0"
ENDPOINTS = ["https://api.indexnow.org/indexnow", "https://www.bing.com/indexnow"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read().decode("utf-8", "replace")


def key_live():
    # Pages-julkaisu voi näkyä CDN:ssä vasta hetken päästä
    for i in range(6):
        try:
            st, body = get(f"{KEY_URL}?t={int(time.time())}")
            if st == 200 and body.strip() == KEY:
                return True
            print(f"IndexNow: avaintiedosto vastasi {st}, sisältö {body.strip()[:60]!r}")
        except Exception as e:
            print("IndexNow: avaintiedostoa ei saatu:", e)
        time.sleep(20)
    return False


def main():
    sm = open(os.path.join(ROOT, "_site", "sitemap.xml"), encoding="utf-8").read()
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", sm) if u.startswith(BASE + "/")][:10000]
    if not urls:
        print("IndexNow: sivukartta on tyhjä, ohitetaan")
        return 0
    if not key_live():
        print(f"IndexNow: {KEY_URL} ei näy oikein livesivulla, ohitetaan")
        return 0
    body = json.dumps({"host": HOST, "key": KEY, "keyLocation": KEY_URL, "urlList": urls}).encode()
    for ep in ENDPOINTS:
        req = urllib.request.Request(ep, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"IndexNow: {ep} vastasi {r.status}, {len(urls)} osoitetta")
                return 0
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300].replace("\n", " ")
            print(f"IndexNow: {ep} vastasi {e.code}: {detail}")
        except Exception as e:
            print(f"IndexNow: {ep} epäonnistui: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
