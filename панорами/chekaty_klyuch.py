"""Чекає на Google Диску папку з назвою KEY_<ключ>, тихо зберігає ключ у google_key.txt
і запускає знімання панорам. Сам ключ ніде не друкується."""
import pathlib, subprocess, sys, time
D = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("G:/Мій диск")
t0 = time.time()
while time.time() - t0 < 3 * 3600:
    try:
        hit = [p for p in ROOT.iterdir() if p.name.upper().startswith("KEY_") and len(p.name) > 20]
    except OSError:
        hit = []
    if hit:
        (D / "google_key.txt").write_text(hit[0].name[4:].strip(), encoding="utf-8")
        print("Ключ отримано, запускаю знімання")
        r = subprocess.run([sys.executable, "-X", "utf8", str(D / "street_view.py")], capture_output=True, text=True, encoding="utf-8")
        print(r.stdout[-3000:]); print(r.stderr[-800:].replace(hit[0].name[4:].strip(), "***"))
        sys.exit(0)
    time.sleep(20)
print("За 3 години папка KEY_ не з'явилась")
