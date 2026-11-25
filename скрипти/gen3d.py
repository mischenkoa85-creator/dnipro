import json, math, sys, base64, io, random
from PIL import Image
from shapely.geometry import Polygon, box, Point, LineString
from shapely.ops import unary_union
from shapely import affinity
d, out = sys.argv[1], sys.argv[2]
z=19
def gxy(lat,lon):
    n=2**z; return (lon+180)/360*n*256,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n*256
mpp=156543.03392*math.cos(math.radians(48.4748))/2**z
# old image origin (zones were digitised there)
o1=tuple(int(v) for v in gxy(48.4762,35.0062))
N,W=48.4778,35.0036
o2=tuple(int(v) for v in gxy(N,W))
im=Image.open(f"{d}/супутник_широкий_z19.jpg"); Wp,Hp=im.size
def mg(gx,gy): return ((gx-o2[0]-Wp/2)*mpp,(gy-o2[1]-Hp/2)*mpp)
def ll(p): return mg(*gxy(p["lat"],p["lon"]))
def oldpx(px,py): return mg(px+o1[0],py+o1[1])
E=json.load(open(f"{d}/osm_широкий.json",encoding="utf-8"))["elements"]
osm={(e["type"],e["id"]):e for e in E}
def poly(i):
    return Polygon([ll(p) for p in osm[("way",i)]["geometry"]])
station=poly(823445052)
hall=Polygon([oldpx(*p) for p in [(1055,660),(1235,910),(905,1065),(860,870)]])
admin=station.difference(hall.buffer(0.5))
if admin.geom_type!="Polygon": admin=max(admin.geoms,key=lambda g:g.area)
def fill(pg, ang, depth, aisle, seg, inset, skip=1):
    c=pg.centroid; r=affinity.rotate(pg.buffer(-inset),-ang,origin=c)
    if r.is_empty: return []
    x0,y0,x1,y1=r.bounds; res=[]; y=y0+0.05; k=0
    while y+depth<=y1+1e-6:
        if k%skip==0:
            x=x0+0.05
            while x+seg<=x1+1e-6:
                b=box(x,y,x+seg,y+depth)
                if r.contains(b):
                    cc=affinity.rotate(b,ang,origin=c).centroid; res.append([round(cc.x,2),round(cc.y,2)])
                x+=seg
        y+=depth+aisle; k+=1
    return res
def main_angle(pg):
    p=list(pg.minimum_rotated_rectangle.exterior.coords)
    e=max(((p[i],p[i+1]) for i in range(4)), key=lambda e: math.dist(*e))
    return math.degrees(math.atan2(e[1][1]-e[0][1], e[1][0]-e[0][0]))
zones=[]
def add(key,name,pg,kind,depth,aisle,seg,inset,dens,yld,h,skip=1):
    a=main_angle(pg); cells=fill(pg,a,depth,aisle,seg,inset,skip)
    area=len(cells)*depth*seg; kw=area*dens/1000
    zones.append(dict(key=key,name=name,kind=kind,ang=round(a,1),depth=depth,seg=seg,h=h,cells=cells,
        area=round(pg.area),parea=round(area),kw=round(kw),mwh=round(kw*yld/1000),
        outline=[[round(x,1),round(y,1)] for x,y in pg.exterior.coords]))
    print(key,round(pg.area),round(area),round(kw),round(kw*yld/1000))
add("C","Навіси над майданчиком автобусів",poly(503943993),"canopy",13,8,2.4,2,210,1040,5.5)
add("D","Навіси над стоянкою зліва",poly(152219807),"canopy",10.5,6.5,2.4,1.5,210,1040,3.2)
add("E","Навіси над малою стоянкою",poly(152219798),"canopy",5.5,6.5,2.4,1,210,1040,3.2)
# ---------- детальний вокзал (за супутником і панорамами 2015 р.) ----------
from shapely.geometry import LineString, MultiPolygon
def P(*pts): return Polygon([oldpx(*q) for q in pts])
parts=[]
def part(pg,h,color,kind="",y0=0,roof=0x6a6f76):
    if pg.geom_type!="Polygon": pg=max(pg.geoms,key=lambda g:g.area)
    parts.append(dict(p=[[round(x,1),round(y,1)] for x,y in pg.exterior.coords],h=h,y0=y0,c=color,k=kind,r=roof))
def sq(px,py,w,l=None,ang=0):
    x,y=oldpx(px,py); l=l or w
    return affinity.rotate(box(x-w/2,y-l/2,x+w/2,y+l/2),ang,origin=(x,y))
Np,Ep,SEp,Sp,Wp_=(1052,655),(1150,735),(1235,905),(905,1062),(862,880)
hall=P(Np,Ep,SEp,Sp,Wp_)
EAVE,RIDGE,SLAB=11.0,13.0,0.8
part(hall,EAVE,0xdfe4ea,"glass")
slab=affinity.scale(hall,1.07,1.07,origin=hall.centroid)
part(slab,SLAB,0x7c8087,"",EAVE,0x55595f)
c0=hall.centroid
def outp(q,z):
    x,y=oldpx(*q); return [round(c0.x+(x-c0.x)*1.07,1),round(c0.y+(y-c0.y)*1.07,1),z]
T=EAVE+SLAB
hallroof=[[outp(Ep,T+2),outp(SEp,T),outp(Sp,T+2)],[outp(Np,T),outp(Ep,T+2),outp(Wp_,T)],[outp(Ep,T+2),outp(Sp,T+2),outp(Wp_,T)]]
ridge=LineString([oldpx(*Ep),oldpx(*Sp)])
rang=math.degrees(math.atan2(ridge.coords[1][1]-ridge.coords[0][1],ridge.coords[1][0]-ridge.coords[0][0]))
dSE=ridge.distance(Point(oldpx(*SEp))); dNW=(ridge.distance(Point(oldpx(*Np)))+ridge.distance(Point(oldpx(*Wp_))))/2
# вентиляційні надбудови вздовж південно-східного краю і дахова установка
vents=[]
for i in range(9):
    f=i/8; q=(1010+(1183-1010)*f, 988+(925-988)*f); v=sq(q[0],q[1],2.6,2.6,rang); vents.append(v); part(v,1.6,0xb9bdc2,"",round(T+2-2*min(1,ridge.distance(Point(oldpx(*q)))/dSE),2))
unit=sq(1203,902,6,3.5,rang); part(unit,2.6,0xe4e6e8,"",round(T+2-2*min(1,ridge.distance(Point(oldpx(1203,902)))/dSE),2))
part(sq(1105,725,2,2,rang),1.2,0xb9bdc2,"",round(T+2-2*min(1,ridge.distance(Point(oldpx(1105,725)))/dNW),2))
obst=unary_union(vents+[unit]).buffer(1.5)
edgeSE=LineString([oldpx(*Sp),oldpx(*SEp)]).buffer(8)
planeSE=P(Ep,SEp,Sp).difference(edgeSE).difference(obst).difference(ridge.buffer(1.5))
planeNW=P(Np,Ep,Sp,Wp_).difference(ridge.buffer(1.5))
def big(g): return g if g.geom_type=="Polygon" else max(g.geoms,key=lambda q:q.area)
cellsA=[]
nA=[]
for pl,dm in ((big(planeSE),dSE),(big(planeNW),dNW)):
    nA.append(len(fill(pl,rang,2.3,0.2,2.4,1.5)))
    for c in fill(pl,rang,2.3,0.2,2.4,1.5):
        d=ridge.distance(Point(c)); cellsA.append([c[0],c[1],round(T+2-2*min(1,d/dm)+0.35,2)])
def addz(key,name,pg,cells,dens,yld,h,ang,kind="roof",depth=4.6,seg=2.4):
    area=len(cells)*depth*seg; kw=area*dens/1000
    zones.append(dict(key=key,name=name,kind=kind,ang=round(ang,1),depth=depth,seg=seg,h=h,cells=cells,area=round(pg.area),parea=round(area),kw=round(kw),mwh=round(kw*yld/1000),outline=[[round(x,1),round(y,1)] for x,y in pg.exterior.coords]))
    print(key,round(pg.area),round(area),round(kw),round(kw*yld/1000))
addz("A","Дах залу (два схили)",hall,cellsA,205,997,T,rang,depth=2.3)
# адмінчастина
wingW=P((622,952),(688,932),(765,1168),(712,1192)); wingE=P((795,930),(835,945),(900,1165),(862,1188))
centre=P((688,932),(795,930),(848,1092),(752,1097)); terr=P((752,1097),(848,1092),(866,1186),(768,1190))
north=P((700,845),(852,850),(872,955),(835,945),(795,930),(688,932))
tower=P((640,800),(702,800),(702,905),(640,925)); step=P((600,850),(640,850),(640,930),(605,940))
WH,CH=12.0,9.0
part(wingW,WH,0xf2f1ec,"ribbon"); part(wingE,WH,0xf2f1ec,"ribbon"); part(centre,CH,0xeceae4,"ribbon"); part(terr,6.5,0xe6e3dc,"")
part(north,14,0xf0eee8,"ribbon"); part(tower,22,0xe9e7e1,""); part(step,15,0xe9e7e1,"")
part(P((700,910),(712,930),(795,962),(800,942)),2.2,0xcfe3ea,"",WH,0xbfd9e2)      # світловий ліхтар між крилами
wang=main_angle(wingW)
for i in range(7):                                                              # ребра ліхтаря над терасою
    f=i/6; part(sq(768+(826-768)*f,1108-3*f,1.0,5.5,wang+90),1.4,0xf4f4f2,"",6.5)
part(P((622,952),(712,1192),(688,1201),(598,961)),1.3,0xd9a520,"",4.3,0xc9c9c4)   # навіс перонів із жовтим фризом
for q in ((1100,655),(1120,690),(1150,690)): pass
part(sq(1150,690,4.2,4.2,0),20,0xb5b3ad,"",0,0x8d8b86)                             # бетонна вентиляційна шахта
# обладнання на даху північного блоку
import random as _r; _r.seed(5)
for q in ((735,880),(760,885),(785,890),(812,895),(838,905),(750,865),(800,870)): part(sq(q[0],q[1],1.6,1.6,0),1.1,0xb9bdc2,"",14)
cellsB=[]
for pg,hh in ((wingW,WH),(wingE,WH),(centre,CH)):
    for c in fill(pg,main_angle(pg),2.3,0.9,2.4,1.5): cellsB.append([c[0],c[1],hh+0.45])
addz("B","Дахи адмінчастини",unary_union([wingW,wingE,centre]).convex_hull,cellsB,205,997,WH,wang,depth=2.3)
# естакади (положення приблизне)
def deck(pts,h0,h1,w=9.0):
    q=[oldpx(*a) for a in pts]; n=len(q)-1
    for i in range(n):
        a,b=q[i],q[i+1]; hh=h0+(h1-h0)*(i+0.5)/n
        part(LineString([a,b]).buffer(w/2,cap_style=2),0.8,0x9a9da1,"",hh-0.8,0x777a7e)
        if hh>2.5: part(box(a[0]-0.6,a[1]-0.6,a[0]+0.6,a[1]+0.6),round(hh-0.8,1),0xa9aaa6,"")
deck([(905,690),(940,628),(1000,588),(1080,574),(1180,590),(1265,640),(1300,715),(1285,800),(1245,885)],5.8,5.8)
deck([(430,1318),(520,1282),(620,1246),(735,1200)],0.8,5.8)
admin=unary_union([wingW,wingE,centre,terr,north,tower,step])
station=unary_union([hall,admin])
def perp_south(a):
    r=math.radians(a); v=(-math.sin(r),math.cos(r))
    if v[1]<0: v=(-v[0],-v[1])
    return round((math.degrees(math.atan2(v[0],-v[1]))%360)-180)
Z={z["key"]:z for z in zones}
Z["A"].update(sc="both",ori=[(3,-53,nA[0]),(3,127,nA[1])],note="по схилах, уздовж гребеня")
Z["B"].update(sc="both",ori=[(10,0,1)],k=0.97,note="ряди 10° на південь")
for k in "CDE": Z[k].update(sc="base",ori=[(7,perp_south(Z[k]["ang"]),1)],note="ряди навісів із проїздами")
# існуючий навіс перонів
canW=P((622,952),(712,1192),(688,1201),(598,961))
cG=[[c[0],c[1],5.75] for c in fill(canW,main_angle(canW),2.3,0.15,2.4,0.3)]
addz("G","Існуючий навіс перонів (захід)",canW,cG,205,997,5.6,main_angle(canW),depth=2.3); zones[-1].update(sc="both",ori=[(3,90,1)],note="по площині навісу")
# північний блок і башта
eq=unary_union([sq(q[0],q[1],1.6,1.6,0) for q in ((735,880),(760,885),(785,890),(812,895),(838,905),(750,865),(800,870))]).buffer(1.2)
cH=[[c[0],c[1],14.45] for c in fill(big(north.difference(eq)),main_angle(north),2.3,0.9,2.4,1.5)]+[[c[0],c[1],22.45] for c in fill(tower,main_angle(tower),2.3,0.9,2.4,1.5)]
addz("H","Північний блок і башта",unary_union([north,tower]).convex_hull,cH,205,997,14,main_angle(north),depth=2.3); zones[-1].update(sc="both",ori=[(10,0,1)],k=0.97,note="між обладнанням")
# навіс над пероном уздовж залу
stripF=P(Np,Wp_,(816,841),(1006,616))
cF=[[c[0],c[1],5.5] for c in fill(stripF,main_angle(stripF),5.5,0.3,2.4,0.4)]
addz("F","Новий навіс над пероном уздовж залу",stripF,cF,210,1040,5.5,main_angle(stripF),kind="canopy",depth=5.5); zones[-1].update(sc="max",ori=[(7,perp_south(main_angle(stripF)),1)],note="смуга 12 м")
# дахи на в'їзді й біля входу (одноповерхові галереї, каси, навіс входу)
ent=[P((1045,1210),(1240,1150),(1250,1185),(1052,1245)),P((835,1300),(1005,1238),(1012,1262),(848,1328)),P((1030,1150),(1040,1120),(1160,1080),(1166,1110)),P((875,1195),(945,1160),(960,1185),(890,1215))]
cJ=[]
for i,g in enumerate(ent):
    hh=4.6 if i==3 else 3.8
    part(g,hh,0xd9d6cf if i<3 else 0xc94a3f,"",0,0xbfc4c9)
    cJ+=[[c[0],c[1],hh+0.3] for c in fill(g,main_angle(g),2.3,0.15,2.4,0.4)]
addz("J","Дахи на в'їзді й біля входу",unary_union(ent).convex_hull,cJ,205,997,3.8,main_angle(ent[0]),depth=2.3); zones[-1].update(sc="both",ori=[(3,0,1)],note="по площині дахів")
zones[-1]["area"]=round(sum(g.area for g in ent))
# півколо навколо залу (якщо це дах над стоянками, а не проїзд)
arc=[oldpx(*a) for a in [(905,690),(940,628),(1000,588),(1080,574),(1180,590),(1265,640),(1300,715),(1285,800),(1245,885)]]
cK=[]; aK=0
for a,b in zip(arc,arc[1:]):
    g=LineString([a,b]).buffer(4.3,cap_style=2); aK+=g.area
    cK+=[[c[0],c[1],6.2] for c in fill(g,math.degrees(math.atan2(b[1]-a[1],b[0]-a[0])),2.3,0.15,2.4,0.3)]
addz("K","Півколо навколо залу",LineString(arc).buffer(4.3),cK,205,997,6.0,0,depth=2.3); zones[-1].update(sc="max",ori=[(3,0,1)],note="якщо зверху дах, а не проїзд")
zones[-1]["area"]=round(aK)
# максимальні карпорти: суцільні навіси
bearly=unary_union([Polygon([ll(q) for q in e["geometry"]]) for e in E if e["type"]=="way" and "building" in e.get("tags",{}) and e["geometry"][0]==e["geometry"][-1] and e["id"]!=823445052]).buffer(2)
for key,i,name,depth,h,ins in (("C2",503943993,"Майданчик автобусів — суцільні навіси",13,5.5,2),("D2",152219807,"Стоянка зліва — суцільні навіси",10.5,3.2,1.5),("E2",152219798,"Мала стоянка — суцільні навіси",5.5,3.2,1)):
    pg=big(poly(i).difference(bearly)); a=main_angle(poly(i))
    cc=fill(pg,a,depth,0.6,2.4,ins)
    addz(key,name,poly(i),cc,210,1040,h,a,kind="canopy",depth=depth); zones[-1].update(sc="max",ori=[(7,perp_south(a),1)],note="перекриває і проїзди")
zones.sort(key=lambda z:z["key"])
H={"garages":3,"roof":4,"warehouse":6,"detached":5,"apartments":16,"church":14,"commercial":9,"office":20,"industrial":8,"retail":8}
bl=[]; bpolys=[]
for e in E:
    t=e.get("tags",{})
    if e["type"]!="way" or "building" not in t or e["id"]==823445052: continue
    g=e["geometry"]
    if g[0]!=g[-1]: continue
    pg=Polygon([ll(p) for p in g])
    if not pg.is_valid or pg.area<20: continue
    if t.get("height"): h=float(t["height"])
    elif t.get("building:levels"): h=float(t["building:levels"])*3.2
    else: h=H.get(t["building"],7)
    bl.append(dict(h=round(h,1),p=[[round(x,1),round(y,1)] for x,y in pg.exterior.coords])); bpolys.append(pg)
allb=unary_union(bpolys+[station]).buffer(1.5)
# rails / tram as lines
lines=[]
for e in E:
    t=e.get("tags",{})
    if e["type"]=="way" and t.get("railway") in("rail","tram"):
        lines.append(dict(k=t["railway"],p=[[round(v,1) for v in ll(p)] for p in e["geometry"]]))
# trees from green pixels
small=im.resize((Wp//8,Hp//8),Image.BOX).convert("RGB"); px=small.load(); random.seed(3)
trees=[]
for j in range(0,small.size[1],4):
    for i in range(0,small.size[0],4):
        r,g,b=px[i,j]
        if g>r*1.18 and g>b*1.25 and g<150 and g>45:   # темна зелень = крони
            x,y=mg(i*8+o2[0]+random.uniform(-10,10),j*8+o2[1]+random.uniform(-10,10))
            if not allb.contains(Point(x,y)) and all(not Polygon(zz["outline"]).contains(Point(x,y)) for zz in zones):
                trees.append([round(x,1),round(y,1),round(random.uniform(5,10),1)])
def cen(e):
    g=e.get("geometry")
    if g: 
        return [round(sum(ll(p)[0] for p in g)/len(g),1), round(sum(ll(p)[1] for p in g)/len(g),1)]
    return [round(v,1) for v in ll(e)]
L=[(("way",823445052),"Автовокзал",20),(("way",80473104),"Готель Premier Abri",24),(("node",935661465),"Трамвай: зупинка «Автовокзал»",8),
   (("way",28169416),"Парк Пам'яті та Примирення",10),(("way",64580240),"ТЦ «Слов'янський»",14),(("way",89116350),"ТРЦ «Колізей»",14),
   (("relation",5374260),"Курчатовський ринок",10),(("node",1035326185),"АЗС ОККО",8),(("way",80473121),"АТБ",12),(("way",80473078),"Прокуратура",12)]
labels=[]
for k,name,h in L:
    e=osm.get(k)
    if not e: print("no",name); continue
    if e["type"]=="relation":
        bb=e.get("bounds")
        if not bb: print("skip",name); continue
        c=[round(v,1) for v in ll(dict(lat=(bb["minlat"]+bb["maxlat"])/2,lon=(bb["minlon"]+bb["maxlon"])/2))]
    else: c=cen(e)
    labels.append(dict(t=name,p=c,h=h))
rail=[l for l in lines if l["k"]=="rail"]
if rail:
    xs=[p for l in rail for p in l["p"]]; labels.append(dict(t="Залізничні колії станції Дніпро-Головний",p=[round(sum(p[0] for p in xs)/len(xs),1),round(sum(p[1] for p in xs)/len(xs),1)],h=8))
for zz in zones:
    if zz["kind"]=="canopy":
        o=zz["outline"]; labels.append(dict(sc=zz["sc"],t="Зона "+zz["key"][0],p=[round(sum(p[0] for p in o)/len(o),1),round(sum(p[1] for p in o)/len(o),1)],h=zz["h"]+6))
im2=im.resize((2000,int(2000*Hp/Wp)),Image.LANCZOS); b=io.BytesIO(); im2.save(b,"JPEG",quality=74)
ltower=[round(v,1) for v in ll(dict(lat=48.47405,lon=35.00893))]
ac=wingW.centroid
# ---------- сонце: питомий виробіток PVGIS по площинах і тінь від оточення ----------
import urllib.request as _u
_pv={}
def pv(tilt,asp):
    if (tilt,asp) not in _pv:
        d=json.loads(_u.urlopen(f"https://re.jrc.ec.europa.eu/api/v5_3/PVcalc?lat=48.4748&lon=35.0087&peakpower=1&loss=14&angle={tilt}&aspect={asp}&outputformat=json",timeout=90).read())
        _pv[(tilt,asp)]=[m["E_m"] for m in d["outputs"]["monthly"]["fixed"]]
    return _pv[(tilt,asp)]
from shapely.strtree import STRtree
obs=[(Polygon(b["p"]),b["h"]) for b in bl]+[(Polygon(q["p"]),q["h"]+q["y0"]) for q in parts]+[(Point(tr[0],tr[1]).buffer(2.5,8),tr[2]) for tr in trees]
tree_=STRtree([o[0] for o in obs]); Hmax=max(o[1] for o in obs)
lat=math.radians(48.4748); suns=[]
for mth in range(12):
    doy=15+30.4*mth; dec=math.radians(23.44)*math.sin(2*math.pi*(284+doy)/365)
    for hr in [x/2 for x in range(8,41)]:
        ha=math.radians((hr-12)*15); el=math.asin(math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha))
        if el<math.radians(4): continue
        az=math.atan2(math.sin(ha),math.cos(ha)*math.sin(lat)-math.tan(dec)*math.cos(lat))+math.pi
        am=1/math.sin(el); suns.append((mth,el,az,1353*0.7**(am**0.678)*math.sin(el)))
def beamloss(cells,h0):
    step=max(1,len(cells)//28); num=[0]*12; den=[0]*12
    for c in cells[::step]:
        hp=c[2] if len(c)>2 else h0; pt=Point(c[0],c[1])
        for mth,el,az,w in suns:
            den[mth]+=w; R=min(450,(Hmax-hp)/math.tan(el))
            if R<=1: continue
            ray=LineString([(c[0],c[1]),(c[0]+math.sin(az)*R,c[1]-math.cos(az)*R)])
            for i in tree_.query(ray):
                pg,top=obs[i]
                if top<=hp+0.4: continue
                it=ray.intersection(pg)
                if it.is_empty: continue
                dd=pt.distance(it)
                if dd<0.3 and top<=hp+2.5: continue
                if top-hp>dd*math.tan(el): num[mth]+=w; break
    return [n/d if d else 0 for n,d in zip(num,den)]
BEAM=0.6
months={"base":[0]*12,"max":[0]*12}
for z in zones:
    wsum=sum(o[2] for o in z["ori"]); mm=[sum(pv(o[0],o[1])[i]*o[2] for o in z["ori"])/wsum*z.get("k",1) for i in range(12)]
    bl_=beamloss(z["cells"],z["h"]+0.3)
    mm2=[mm[i]*(1-BEAM*bl_[i]) for i in range(12)]
    z["spec"]=round(sum(mm2)); z["shade"]=round((1-sum(mm2)/sum(mm))*100,1); z["mwh"]=round(z["kw"]*sum(mm2)/1000)
    z["tilt"]=z["ori"][0][0]; z["asp"]=[o[1] for o in z["ori"]]
    for s in ("base","max"):
        if z["sc"] in (s,"both"):
            for i in range(12): months[s][i]+=z["kw"]*mm2[i]/1000
    print(z["key"],z["name"],"|",z["area"],"м2 | панелі",z["parea"],"м2 |",z["kw"],"кВт |",z["spec"],"кВт·год/кВт | тінь",z["shade"],"% |",z["mwh"],"МВт·год |",z["sc"])
    del z["ori"]
months={s:[round(v,1) for v in months[s]] for s in months}
for s in ("base","max"):
    print(s,"кВт",sum(z["kw"] for z in zones if z["sc"] in (s,"both")),"МВт·год",round(sum(months[s])),"червень/доба",round(months[s][5]/30,1),"грудень/доба",round(months[s][11]/31,1))
data=dict(months=months,parts=parts,hallroof=hallroof,tower=ltower,sign=[round(ac.x,1),round(ac.y,1)],w=round(Wp*mpp,1),h=round(Hp*mpp,1),zones=zones,buildings=bl,trees=trees,lines=lines,labels=labels,
  
  month_roof=[22,39,75,104,136,146,148,133,95,58,26,16], month_can=[28,47,84,112,142,150,154,144,106,70,33,21])
json.dump(data,open(f"{out}/data.json","w",encoding="utf-8"),ensure_ascii=False)
open(f"{out}/sat.b64","w").write(base64.b64encode(b.getvalue()).decode())
print("size m",data["w"],data["h"],"img kb",len(b.getvalue())//1024,"buildings",len(bl),"trees",len(trees),"lines",len(lines),"labels",len(labels),"kW",sum(z["kw"] for z in zones),"MWh",sum(z["mwh"] for z in zones))
