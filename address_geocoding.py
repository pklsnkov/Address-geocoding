import pandas as pd
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point

df = pd.read_excel('Таблица адресов.xlsx')
output_file = 'output.gpkg'

previous_uchastok = None

lists_geodata = []
for index, row in df.iterrows():
     bounds_original = row['Границы участка']
     if 'дома' in row['Границы участка']:
          row['Границы участка'] = row['Границы участка'].replace('дома', 'дом')
     # if ',' not in row['Границы участка']:
     #      continue
     
     address = row['Границы участка'].replace('дом №', '').split('(с')[0]
     address = address.replace('  ', '')
     
     location = ox.geocode(f'Москва, {address}')
     point = Point(location[1], location[0])
     
     nomer_uchastka = row['Номер участка']
     if pd.isna(nomer_uchastka):
          if previous_uchastok is not None:
               nomer_uchastka = previous_uchastok

     list_geodata = [int(nomer_uchastka), bounds_original, point]
     lists_geodata.append(list_geodata)
     previous_uchastok = nomer_uchastka 

gdf = gpd.GeoDataFrame(lists_geodata, columns=['Номер участка', 'Границы участка', 'geometry'])
gdf = gdf.set_geometry('geometry')
gdf.to_file(output_file, driver="GPKG")
