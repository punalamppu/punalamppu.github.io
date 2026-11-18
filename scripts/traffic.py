"""Hakee kävijätilastot GoatCounterista tiedostoon data/liikenne.json (kerran päivässä).

Vaatii repon salaisuuden GOATCOUNTER_TOKEN (GoatCounter → Settings → API, oikeus "Read statistics").
Tallentaa vain kootut luvut: päivittäiset käynnit 60 päivältä sekä 30 päivän suosituimmat sivut ja lähteet.
"""
import datetime as dt, json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://punalamppu.goatcounter.com/api/v0"
TOKEN = (os.environ.get("GOATCOUNTER_TOKEN") or "").strip()


def get(path, **q):
    url = API + path + "?" + "&".join(f"{k}={v}" for k, v in q.items())
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    if not TOKEN:
        print("Liikenne: GOATCOUNTER_TOKEN puuttuu, ohitetaan")
        return 0
    today = dt.date.today()
    s60, s30 = (today - dt.timedelta(days=60)).isoformat(), (today - dt.timedelta(days=30)).isoformat()
    end = (today + dt.timedelta(days=1)).isoformat()
    out = {"haettu": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")}
    try:
        t = get("/stats/total", start=s60, end=end)
        out["paivat"] = {x["day"][:10]: x.get("daily", 0) for x in t.get("stats") or []}
        out["yhteensa60"] = t.get("total")
    except Exception as e:
        print("Liikenne: kokonaismäärä epäonnistui:", e)
    try:
        h = get("/stats/hits", start=s30, end=end, limit=25)
        out["sivut30"] = [{"polku": x.get("path"), "otsikko": (x.get("title") or "")[:90], "kaynnit": x.get("count")} for x in h.get("hits") or []]
    except Exception as e:
        print("Liikenne: sivut epäonnistuivat:", e)
    try:
        r = get("/stats/toprefs", start=s30, end=end, limit=20)
        out["lahteet30"] = [{"lahde": x.get("name") or "(suora)", "kaynnit": x.get("count")} for x in r.get("stats") or []]
    except Exception as e:
        print("Liikenne: lähteet epäonnistuivat:", e)
    if len(out) == 1:
        return 0
    p = os.path.join(ROOT, "data", "liikenne.json")
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    d = out.get("paivat") or {}
    last7 = sum(v for k, v in d.items() if k > (today - dt.timedelta(days=7)).isoformat())
    print(f"Liikenne: 7 päivää {last7} käyntiä, 60 päivää {out.get('yhteensa60')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
