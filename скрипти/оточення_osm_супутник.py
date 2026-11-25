import math, io, json, sys, urllib.request, urllib.parse, collections
from PIL import Image
out=sys.argv[1]
S,W,N,E = 48.4716, 35.0036, 48.4778, 35.0138
UA={"User-Agent":"site-survey/1.0"}
def get(u,data=None): return urllib.request.urlopen(urllib.request.Request(u,data=data,headers=UA),timeout=120).read()
def xy(lat,lon,z):
    n=2**z; return (lon+180)/360*n,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
z=19
x0,y0=xy(N,W,z);x1,y1=xy(S,E,z);X0,Y0,X1,Y1=int(x0),int(y0),int(x1),int(y1)
im=Image.new("RGB",((X1-X0+1)*256,(Y1-Y0+1)*256))
for x in range(X0,X1+1):
    for y in range(Y0,Y1+1):
        im.paste(Image.open(io.BytesIO(get(f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"))),((x-X0)*256,(y-Y0)*256))
im=im.crop((int((x0-X0)*256),int((y0-Y0)*256),int((x1-X0)*256),int((y1-Y0)*256))); im.save(f"{out}/супутник_широкий_z19.jpg",quality=90); print(im.size)
bb=f"({S},{W},{N},{E})"
q=f'[out:json][timeout:90];(way["building"]{bb};nwr["power"]{bb};nwr["railway"]{bb};way["highway"]{bb};nwr["amenity"]{bb};nwr["public_transport"]{bb};nwr["natural"]{bb};way["landuse"]{bb};way["leisure"]{bb};nwr["tourism"]{bb};nwr["shop"]{bb};nwr["office"]{bb};way["barrier"]{bb};);out tags geom;'
d=json.loads(get("https://overpass-api.de/api/interpreter",urllib.parse.urlencode({"data":q}).encode()))
open(f"{out}/osm_широкий.json","w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False))
c=collections.Counter()
for e in d["elements"]:
    t=e.get("tags",{})
    for k in ("building","power","railway","highway","amenity","public_transport","natural","landuse","leisure","tourism","shop","office"):
        if k in t: c[f"{k}={t[k]}"]+=1
print(len(d["elements"])); print(c.most_common(70))
print("--- named / power")
for e in d["elements"]:
    t=e.get("tags",{})
    if "power" in t or (t.get("name") and ("building" in t or "amenity" in t or "railway" in t or "tourism" in t or "leisure" in t)):
        print(e["type"],e["id"],{k:v for k,v in t.items() if k in("name","power","building","building:levels","amenity","railway","tourism","leisure","voltage","substation","operator","height")})
