import geopandas as gpd
from shapely.geometry import Point, MultiPolygon, Polygon

def fix_coordinates(geometry):
    if isinstance(geometry, MultiPolygon):
        return MultiPolygon([fix_coordinates(poly) for poly in geometry.geoms])
    elif isinstance(geometry, Polygon):
        return Polygon([(point[1], point[0]) if isinstance(point, tuple) else (point.y, point.x) for point in geometry.exterior.coords])
    elif isinstance(geometry, Point):
        return Point(geometry.y, geometry.x) if hasattr(geometry, 'y') else Point(geometry[1], geometry[0])
    else:
        return geometry

def fix_geopackage(input_path, output_path):
    gdf = gpd.read_file(input_path)
    gdf['geometry'] = gdf['geometry'].apply(fix_coordinates)
    gdf.to_file(output_path, driver='GPKG')

fix_geopackage('voting_room.gpkg', 'voting_room_sw.gpkg')
