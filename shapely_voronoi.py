from shapely import Polygon, Point, MultiPoint, MultiPolygon, LineString
from shapely.ops import voronoi_diagram
import geopandas as gpd
import matplotlib.pyplot as plt
from longsgis import voronoiDiagram4plg
import pandas as pd

def plot_polygon(polygon, ax, facecolor="blue", alpha=0.5):
    """plots a polygon with its interior in matplotlib"""
    poly = gpd.GeoSeries([polygon])
    poly.plot(ax=ax, edgecolor="Black", facecolor=facecolor, alpha=alpha)

def calc_polygon(poly, multiplier):
    new_polygon_points = []

    for i in range(len(poly.exterior.coords) - 1):
        p1 = poly.exterior.coords[i]
        p2 = poly.exterior.coords[i + 1]
        
        edge_length = LineString([p1, p2]).length
        
        num_points = int(edge_length * multiplier)
        
        delta_x = (p2[0] - p1[0]) / (num_points + 1)
        delta_y = (p2[1] - p1[1]) / (num_points + 1)
        
        for j in range(0, num_points + 2):
            new_point = Point(p1[0] + j * delta_x, p1[1] + j * delta_y)
            new_polygon_points.append(new_point)

    return Polygon(new_polygon_points)

fig, ((ax1, ax2), (ax3, ax4))  = plt.subplots(2, 2, figsize=(15, 15))
#overlapping
#points = [(0, 2), (2, 0), (4, 2), (2, 4), (3, 2), (5, 0), (7, 2), (5, 4)]
# intersecting
#points = [(-0.5, 2), (1.5, 0), (3.5, 2), (1.5, 4), (3.5, 2), (5.5, 0), (7.5, 2), (5.5, 4)]
# some real points that do not work
points = [(1.23, 1.38), (0.93, 1.08), (0.63, 1.38), (0.93, 1.68), (1, 0.79), (0.7, 0.49), (0.40, 0.79), (0.70, 1.09)]

shapely_points = MultiPoint([Point(pt) for pt in points])

poly1 = Polygon(points[0:4])
poly2 = Polygon(points[4:])

poly3 = calc_polygon(poly1, multiplier=10)
poly4 = calc_polygon(poly2, multiplier=10)

regions = voronoi_diagram(shapely_points)
plot_polygon(poly1, ax1, facecolor="green")
plot_polygon(poly2, ax1, facecolor="green")
for poly in regions.geoms:
    plot_polygon(poly, ax1)
for point in points:
    ax1.scatter(point[0], point[1], c="red")
data_frame = pd.DataFrame()
data_frame['geometry'] = [poly1, poly2]
data_frame['area'] = data_frame['geometry'].apply(lambda x: x.area)
data_frame = gpd.GeoDataFrame(data_frame[["area", "geometry"]])
vd = voronoiDiagram4plg(data_frame, Polygon([(-4, -5), (12, -5), (12, 10), (-4, 10)]))
for poly in vd["geometry"]:
    plot_polygon(poly, ax2)
for point in points:
    ax2.scatter(point[0], point[1], c="red")
shapely_polygons = MultiPolygon([poly1, poly2])
regions = voronoi_diagram(shapely_polygons)

regions = voronoi_diagram(MultiPolygon([poly3, poly4]))
for poly in regions.geoms:
    plot_polygon(poly, ax3)
for point in poly3.exterior.coords:
    ax3.scatter(point[0], point[1], c="red")
for point in poly4.exterior.coords:
    ax3.scatter(point[0], point[1], c="red")

data_frame = pd.DataFrame()
data_frame['geometry'] = [poly3, poly4]
data_frame['area'] = data_frame['geometry'].apply(lambda x: x.area)
data_frame = gpd.GeoDataFrame(data_frame[["area", "geometry"]])
vd = voronoiDiagram4plg(data_frame, Polygon([(-4, -5), (12, -5), (12, 10), (-4, 10)]))
print(vd)
for poly in vd["geometry"]:
    plot_polygon(poly, ax4)
for point in poly3.exterior.coords:
    ax4.scatter(point[0], point[1], c="red")
for point in poly4.exterior.coords:
    ax4.scatter(point[0], point[1], c="red")

#plt.savefig("not_touching_ped.png", bbox_inches='tight')
#plt.show()