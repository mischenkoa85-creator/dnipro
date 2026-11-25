import math, io, json, sys, urllib.request, urllib.parse
from PIL import Image, ImageDraw
out = sys.argv[1]
S,W,N,E = 48.4732, 35.0062, 48.4762, 35.0112
UA = {"User-Agent":"site-survey/1.0"}
def get(u, data=None):
    return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=UA), timeout=60).read()
def xy(lat, lon, z):
    n = 2**z
    return (lon+180)/360*n, (1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n
def mosaic(z, name):
    x0,y0 = xy(N,W,z); x1,y1 = xy(S,E,z)
    X0,Y0,X1,Y1 = int(x0),int(y0),int(x1),int(y1)
    im = Image.new("RGB", ((X1-X0+1)*256, (Y1-Y0+1)*256))
    for x in range(X0,X1+1):
        for y in range(Y0,Y1+1):
            t = get(f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")
            im.paste(Image.open(io.BytesIO(t)), ((x-X0)*256,(y-Y0)*256))
    box = (int((x0-X0)*256), int((y0-Y0)*256), int((x1-X0)*256), int((y1-Y0)*256))
    im = im.crop(box); im.save(f"{out}/{name}", quality=92)
    return im, (X0,Y0,box)
im, ref = mosaic(19, "супутник_z19.jpg")
print("z19", im.size)
# OSM
q = f'[out:json][timeout:60];(way["building"]({S},{W},{N},{E});way["amenity"~"bus_station|parking"]({S},{W},{N},{E});way["highway"="platform"]({S},{W},{N},{E});way["public_transport"]({S},{W},{N},{E}););out tags geom;'
d = json.loads(get("https://overpass-api.de/api/interpreter", urllib.parse.urlencode({"data":q}).encode()))
open(f"{out}/osm.json","w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False))
def area(g):
    lat0 = math.radians(g[0]["lat"]); R=6371000
    p=[(math.radians(a["lon"])*R*math.cos(lat0), math.radians(a["lat"])*R) for a in g]
    return abs(sum(p[i][0]*p[i+1][1]-p[i+1][0]*p[i][1] for i in range(len(p)-1)))/2
dr = ImageDraw.Draw(im); X0,Y0,box = ref
rows=[]
for e in d["elements"]:
    g=e.get("geometry");
    if not g or g[0]!=g[-1]: continue
    a=area(g); t=e.get("tags",{})
    rows.append((a,e["id"],t))
    if "building" in t:
        pts=[((xy(p["lat"],p["lon"],19)[0]-X0)*256-box[0], (xy(p["lat"],p["lon"],19)[1]-Y0)*256-box[1]) for p in g]
        dr.line(pts, fill=(255,230,0), width=3)
        cx=sum(p[0] for p in pts)/len(pts); cy=sum(p[1] for p in pts)/len(pts)
        if a>300: dr.text((cx-20,cy), f"{a:.0f} m2", fill=(255,255,255))
im.save(f"{out}/супутник_z19_контури.jpg", quality=92)
for a,i,t in sorted(rows, key=lambda r:-r[0])[:25]:
    print(round(a), i, {k:v for k,v in t.items() if k in("building","name","amenity","building:levels","roof:shape","highway","public_transport","covered","parking")})
