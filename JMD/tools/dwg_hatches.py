"""Extract closed hatch boundaries from dwg.json (LibreDWG export) -> hatches.json (+ diagnostic plot hatch.png). Run in the folder holding dwg.json."""
import json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP
E=json.load(open('dwg.json'))['entities']
def bulge_pts(vs, closed=True):
    out=[]; n=len(vs)
    for i in range(n if closed else n-1):
        a=vs[i]; b=vs[(i+1)%n]; out.append((a['x'],a['y'])); bu=a.get('bulge',0) or 0
        if abs(bu)>1e-9:
            th=4*math.atan(bu); dx=b['x']-a['x']; dy=b['y']-a['y']; c=math.hypot(dx,dy)
            if c<1e-9: continue
            d=c/(2*math.tan(th/2)); R=abs(c/(2*math.sin(th/2)))
            cx=(a['x']+b['x'])/2-dy/c*d; cy=(a['y']+b['y'])/2+dx/c*d
            a0=math.atan2(a['y']-cy,a['x']-cx); k=max(4,int(abs(th)*R/2))
            out += [(cx+R*math.cos(a0+th*j/k), cy+R*math.sin(a0+th*j/k)) for j in range(1,k)]
    return out
def edge_pts(bp):
    pts=[]
    for ed in bp.get('edges',[]):
        t=ed.get('type')
        if t==1: pts += [(ed['start']['x'],ed['start']['y']),(ed['end']['x'],ed['end']['y'])]
        elif t==2:
            cx,cy=ed['center']['x'],ed['center']['y'];r=ed['radius'];s=ed['startAngle'];e=ed['endAngle']
            if ed.get('isCCW',1):
                if e<s: e+=2*math.pi
            else:
                s,e=-s,-e
                if e>s: e-=2*math.pi
            k=max(6,int(abs(e-s)*r/2)); pts+=[(cx+r*math.cos(s+(e-s)*i/k), cy+r*math.sin(s+(e-s)*i/k)) for i in range(k+1)]
        else:
            for key in ('controlPoints','fitDatum'):
                if ed.get(key): pts += [(p['x'],p['y']) for p in ed[key]]; break
    return pts
res=[]
for h in [e for e in E if e['type']=='HATCH']:
    for bp in h['boundaryPaths']:
        pts = bulge_pts(bp['vertices']) if 'vertices' in bp and bp['vertices'] else edge_pts(bp)
        if len(pts)>2: res.append({'layer':h['layer'],'pat':h['patternName'],'ci':h['colorIndex'],'pts':pts})
json.dump(res,open('hatches.json','w'))
from shapely.geometry import Polygon
fig,ax=plt.subplots(figsize=(18,18),dpi=100)
import random
for i,r in enumerate(res):
    P=Polygon(r['pts']); c=plt.cm.tab20(i%20)
    ax.add_patch(MP(r['pts'],closed=True,fc=c,ec='k',lw=.4,alpha=.6))
    ce=P.representative_point() if P.is_valid else P.centroid
    ax.text(ce.x,ce.y,f"{i}:{r['pat']}/{r['ci']}\n{P.area:.0f}",fontsize=6)
for e in E:
    if e['type']=='MTEXT' and e['layer']=='Layer1':
        p=e['insertionPoint']; ax.text(p['x'],p['y'],e['text'].replace('\\P',' ')[:18],fontsize=4,color='b')
ax.set_xlim(860,1840); ax.set_ylim(1220,2220); ax.set_aspect('equal')
plt.savefig('hatch.png',bbox_inches='tight')
print(len(res))

# ---- enrich: labels inside each hatch, area, rectangle dims, centroid (consumed by prep_model.py)
from shapely.geometry import Point
labels = [(Point(e['insertionPoint']['x'], e['insertionPoint']['y']), e['text'].replace('\\P', ' ').strip().lower())
          for e in E if e['type'] == 'MTEXT' and e['layer'] == 'Layer1']
for h in res:
    P = Polygon(h['pts']).buffer(0)
    h['labs'] = sorted(set(l for p, l in labels if P.buffer(1).contains(p)))
    c = list(P.minimum_rotated_rectangle.exterior.coords)
    a, b = math.dist(c[0], c[1]), math.dist(c[1], c[2])
    h['area'] = P.area; h['dims'] = (round(min(a, b), 1), round(max(a, b), 1)); h['cen'] = (round(P.centroid.x), round(P.centroid.y))
json.dump(res, open('hatches.json', 'w'))
