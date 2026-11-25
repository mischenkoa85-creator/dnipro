import sys, pathlib
from playwright.sync_api import sync_playwright
src=pathlib.Path(sys.argv[1]); out=sys.argv[2]
tmp=pathlib.Path(out)/"t.html"
tmp.write_text('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font:14px system-ui}[hidden]{display:none!important}</style></head><body>'+src.read_text(encoding="utf-8")+'</body></html>',encoding="utf-8")
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True,args=["--use-gl=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
    for name,vp in (("pc",{"width":1400,"height":900}),("tel",{"width":390,"height":844})):
        pg=b.new_page(viewport=vp); errs=[]
        pg.on("console",lambda m:errs.append(m.text) if m.type=="error" else None); pg.on("pageerror",lambda e:errs.append(str(e)))
        pg.goto(tmp.as_uri()); pg.wait_for_timeout(5000); pg.screenshot(path=f"{out}/{name}_1.png")
        pg.get_by_role("button",name="Максимальний").click(); pg.get_by_role("button",name="Дах вокзалу").click(); pg.wait_for_timeout(1800); pg.screenshot(path=f"{out}/{name}_2.png")
        pg.get_by_role("button",name="Цифри").click(); pg.wait_for_timeout(800); pg.screenshot(path=f"{out}/{name}_3.png")
        print(name,"errors:",errs)
    b.close()
