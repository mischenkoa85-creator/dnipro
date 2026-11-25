"""Знімки панорам Google Street View навколо автовокзалу.
Ключ читається з файлу google_key.txt поруч (один рядок). Ключ ніде не друкується."""
import json, pathlib, sys, urllib.request, urllib.parse
D = pathlib.Path(__file__).resolve().parent
kf = D / "google_key.txt"
if not kf.exists() or not kf.read_text(encoding="utf-8").strip():
    sys.exit("Немає ключа: впишіть його у файл google_key.txt")
KEY = kf.read_text(encoding="utf-8").strip()
POINTS = {  # назва: (широта, довгота, [напрямки камери])
    "01_фасад_з_вулиці":      (48.47385, 35.00905, [300, 330, 0, 30]),
    "02_вхід_зліва":          (48.47400, 35.00830, [0, 40, 80]),
    "03_мала_стоянка":        (48.47365, 35.00960, [270, 310, 350]),
    "04_майданчик_автобусів": (48.47470, 35.00760, [200, 250, 290, 340]),
    "05_стоянка_зліва":       (48.47420, 35.00720, [0, 60, 300]),
    "06_готель_і_вежа":       (48.47400, 35.01030, [330, 20, 70]),
    "07_вулиця_захід":        (48.47360, 35.00780, [20, 60, 100]),
    "08_вулиця_схід":         (48.47390, 35.01080, [250, 290, 330]),
}
def get(url, params):
    q = urllib.parse.urlencode({**params, "key": KEY})
    return urllib.request.urlopen(f"{url}?{q}", timeout=60).read()
log = {}
for name, (lat, lon, heads) in POINTS.items():
    try:
        m = json.loads(get("https://maps.googleapis.com/maps/api/streetview/metadata",
                           {"location": f"{lat},{lon}", "radius": 60, "source": "outdoor"}))
    except Exception as e:
        print(name, "помилка запиту:", type(e).__name__); continue
    log[name] = {k: m.get(k) for k in ("status", "date", "location", "pano_id", "copyright")}
    print(name, m.get("status"), m.get("date"))
    if m.get("status") != "OK":
        continue
    for h in heads:
        img = get("https://maps.googleapis.com/maps/api/streetview",
                  {"pano": m["pano_id"], "size": "640x640", "scale": 2, "heading": h, "pitch": 12, "fov": 90})
        (D / f"{name}_{h:03d}.jpg").write_bytes(img)
(D / "panoramy.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
print("Готово")
