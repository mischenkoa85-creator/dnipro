"""Приблизна економіка СЕС автовокзалу Дніпро. Ціни — з КП E-Systems (Форель ES-131126-01, Агро-Еталон ES-101126-01),
решта — припущення, позначені в P. Усі суми в USD без ПДВ."""
import json, pathlib, sys
D = pathlib.Path(__file__).resolve().parent.parent
Z = json.loads((D/"3d"/"data.json").read_text(encoding="utf-8"))["zones"]
months = json.loads((D/"3d"/"data.json").read_text(encoding="utf-8"))["months"]
P = dict(
    panel=123500/1692/730,        # $/Вт, ZNSHINE 730 Вт FOB (Агро-Еталон: 123 500 $ / 1 692 шт)
    inverter=34400/9/125000,      # $/Вт, GoodWe GW125K-GT (Форель: 34 400 $ / 9 шт)
    cable=(12000+13500+6700)/1326000*1.25,  # $/Вт, кабелі, щити (Форель) +25 % на довші траси навісів
    mount_roof=26100/1326000,     # $/Вт, кріплення на дах (Форель)
    mount_flat=0.040,             # $/Вт, рами 3° на пласких дахах — припущення
    frame_skylight=0.150,         # $/Вт, рама над ліхтарем і терасою — припущення
    canopy_bus=0.300,             # $/Вт, сталевий навіс над автобусами 13 м, 5,5 м, з фундаментами — припущення
    canopy_car=0.200,             # $/Вт, навіс над легковими 3,2 м — припущення
    delivery=0.025,               # $/Вт, море Шанхай–Констанца, розмитнення, авто (≈600 панелей на 40′HQ) — оцінка
    install_roof=0.120,           # $/Вт, монтаж і електромонтаж на даху (Форель ≈0,15 з краном і щитами)
    install_canopy=0.100,         # $/Вт, монтаж панелей і електрика на навісах
    grid=0.050,                   # $/Вт, ТП 10/0,4 кВ, приєднання, облік — припущення
    services=0.10,                # частка: проєкт, закупівля, нагляд (E-Systems під ключ)
    reserve=0.10,                 # частка: резерв концепції
    price=160.0,                  # $/МВт·год, вартість власної енергії (≈7 грн/кВт·год з розподілом, курс 43,8)
    om=0.015, degr=0.004, rate=0.10, years=20,
)
def mount(z):
    k = z["key"]
    if k in ("C","C2"): return P["canopy_bus"]
    if z["kind"]=="canopy" or k in ("K","L","F"): return P["canopy_car"] if k in ("D","D2","E","E2","F","K","L") else P["canopy_bus"]
    if k=="B": return P["mount_flat"]*0.8+P["frame_skylight"]*0.2
    if k in ("H","J","G"): return P["mount_flat"]
    return P["mount_roof"]
def capex(zs):
    eq=dl=st=0
    for z in zs:
        w=z["kw"]*1000
        eq+=w*(P["panel"]+P["inverter"]+P["cable"]); dl+=w*P["delivery"]
        can = z["kind"]=="canopy" or z["key"] in ("K","L","F")
        st+=w*(mount(z)+(P["install_canopy"] if can else P["install_roof"])+P["grid"])
    base=eq+dl+st; srv=base*P["services"]; res=(base+srv)*P["reserve"]
    return dict(eq=eq,dl=dl,st=st,srv=srv,res=res,tot=base+srv+res)
def finance(cap, mwh, price):
    cf=[-cap]; cum=-cap; pb=None
    for y in range(1,P["years"]+1):
        v=mwh*(1-P["degr"])**(y-1)*price - cap*P["om"]
        cf.append(v); prev=cum; cum+=v
        if pb is None and cum>=0: pb=y-1+(-prev)/v
    npv=sum(c/(1+P["rate"])**i for i,c in enumerate(cf))
    lo,hi=-0.99,1.0
    for _ in range(200):
        m=(lo+hi)/2; f=sum(c/(1+m)**i for i,c in enumerate(cf))
        lo,hi=(m,hi) if f>0 else (lo,m)
    return pb,npv,m
out={}
for s in ("base","max"):
    zs=[z for z in Z if z["sc"] in (s,"both")]
    kw=sum(z["kw"] for z in zs); mwh=sum(months[s]); c=capex(zs)
    r=dict(n=sum(z["n"] for z in zs),kw=kw,mwh=round(mwh),**{k:round(v) for k,v in c.items()},
           perW=round(c["tot"]/kw/1000,3))
    for name,pr in (("low",120),("mid",P["price"]),("high",200)):
        pb,npv,irr=finance(c["tot"],mwh,pr)
        r[name]=dict(price=pr,effect=round(mwh*pr),payback=round(pb,1) if pb else None,npv=round(npv),irr=round(irr*100,1))
    out[s]=r
    print(s, json.dumps(r,ensure_ascii=False))
(D/"дані"/"економіка.json").write_text(json.dumps(dict(assumptions=P,result=out),ensure_ascii=False,indent=1),encoding="utf-8")
