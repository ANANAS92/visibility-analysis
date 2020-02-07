from shapely.geometry import Point,Polygon,LineString,MultiPoint
from pyproj import Proj, transform
import geopandas as gpd
from matplotlib import pyplot
from descartes import PolygonPatch

import visibility_analysis as va

def change_coord (point, s1,s2):
    g = Point(transform(Proj(init='EPSG:'+str(s1)),Proj(init='EPSG:'+str(s2)),point[0],point[1]))
    return (g.coords[:][0])

######################DATA##################################
Buildings = gpd.GeoDataFrame.from_file('Data/data/Polygons.shp', encoding='utf-8').replace({-999: None}).to_crs({'init': 'epsg:3857'})
B={}
for b in range(len(Buildings.Sys)):
    if Buildings.geometry[b].geom_type=="MultiPolygon":# if building is multipilygon, it is better to consider parts of the building separately
        for r in Buildings.geometry[b]:
            B[r.centroid.coords[0]]=r.buffer(0) # we use 0buffer not to check the validity of the geometry
    else:
        B[Buildings.geometry[b].centroid.coords[0]]=Buildings.geometry[b].buffer(0)


del Buildings,b

######################################################
R_observation = 500 #radius of observation 
Sub_B,sorted_Building = {},{}

fig, ax = pyplot.subplots(num=None, figsize=(10, 10), dpi=50)
# observation point
ob_p = va.change_coord ((30.3074411644341,59.9159819328356), '4326','3857') #change coordinate system
ax.plot(ob_p[0], ob_p[1],'o', color='red',markersize=5)
#observation area
Area = Point(ob_p).buffer(R_observation) #create an observation area
XY = Area.bounds#min and max point of the observation area
#ax.add_patch(PolygonPatch(Area, fc='w', ec='k', alpha=0.5, zorder=1))
holes, VisArea = va.VA (ob_p,B,Area,R_observation)
for build in holes:
    ax.add_patch(PolygonPatch(build[0], fc='gray', ec='gray', alpha=0.2, zorder=1))
ax.add_patch(PolygonPatch(VisArea, fc='green', ec='green', alpha=0.2, zorder=1))

del_x=120
xrange = [XY[0]-del_x, XY[2]+del_x]
yrange = [XY[1]-del_x, XY[3]+del_x]
ax.set_xlim(*xrange)
ax.set_ylim(*yrange)
ax.set_aspect(1)
pyplot.show()
ax.clear()
