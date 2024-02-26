'''
Основной код
'''

import pandas as pd
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import requests

from decimal import Decimal

from yandex_geocoder import Client
from config import client_api
client = Client(client_api)

df = pd.read_excel('Таблица адресов.xlsx')

previous_uchastok = None
previous_uik = None
previous_voting_room = None

lists_geodata = []
lists_uik = []
lists_voting_room = []

exceptions_file = 'exceptions.txt'

with open(exceptions_file, 'w') as file:
     pass

def list2geom(list):
     polygons = []
     for polygon_list in list:
          polygon = Polygon(polygon_list)
          polygons.append(polygon)
     if len(polygons) > 1:
          return MultiPolygon(polygons)
     else:
          return polygon

def address2coords(address, radius=5, num_of_endeavor=0):
     if num_of_endeavor > 2:
          return None
     coordinates = client.coordinates(f"Москва, {address}")
     float_coords = tuple(float(coord) for coord in coordinates)
     # float_coords = float_coords[::-1]
     lat_point = float_coords[1]
     lon_point = float_coords[0]
     
     overpass_api_base_url = "https://overpass-api.de/api/interpreter?data="
     # lat_point = 55.75939
     # lon_point = 37.636958
     coords_url = f"""
          [out:json];
          (
               relation["building"](around:{radius},{lat_point},{lon_point});
               way["building"](around:{radius},{lat_point},{lon_point});
          );
          out geom;
     """
     
     overpass_response = requests.get(f"{overpass_api_base_url}{coords_url}")
     if overpass_response.status_code == 200:
          response_json = overpass_response.json()
          if len(response_json['elements']) > 1:
               num_of_endeavor+=1
               polygon = address2coords(address, 3, num_of_endeavor)
               return polygon
          elif len(response_json['elements']) == 0:
               num_of_endeavor+=1
               # print("Не найдено зданий")
               polygon = address2coords(address, 10, num_of_endeavor)
               return polygon
          else:
               element = response_json['elements'][0]
          
          polygon = []
          first_elem_flag = True
          
          members = []
          try:
               members = element['members']
          except:
               members.insert(0, element)
          # if len(element['members']) != 1:
          # # if element['type'] == 'relation':
          #      members = element['members']
          # else:
          #      members.insert(0, element)
          for member in members:
               poly = []
               for geom in member['geometry']: poly.append([geom['lat'],geom['lon']])
               if len(poly) > 2:
                    polygon.insert(0, poly) if first_elem_flag else polygon.append(poly)
                    first_elem_flag = False
               # else:
                    # print(f"Возникли проблемы, количество точек: {len(poly)}")
          return polygon
     else:
          return None
    

def address_parse(address, exceptions_file, type):
     try:
          coords_list = address2coords(address)
          geometries = list2geom(coords_list)
          if geometries is not None: 
               print(f"Сделано {address}")
               return geometries
     except Exception as e:
          print(e)
          address_orig = address
          address = address.replace('дом №', '')
          
          if '-ый' in address: address = address.replace('-ый', '-й')
          if '-ой' in address: address = address.replace('-ой', '-й')
          if '-ий' in address: address = address.replace('-ий', '-й')
          
          if '_x0002_' in address: address = address.replace('_x0002_', '-')
          
          if '(корп' in address:
               address_list = address.split('(корп')
               address = f"{address_list[0]}к{address_list[1]}".replace(')', '')
          if '(корп.' in address:
               address_list = address.split('(корп.')
               address = f"{address_list[0]}к{address_list[1]}".replace(')', '')
          if '(стр.' in address:
               address_list = address.split('(стр.')
               address = f"{address_list[0]}с{address_list[1]}".replace(')', '')
          if '(стр' in address:
               address_list = address.split('(стр')
               address = f"{address_list[0]}с{address_list[1]}".replace(')', '')
          if '(кор' in address:
               address_list = address.split('(кор')
               address = f"{address_list[0]}к{address_list[1]}".replace(')', '')
          
          while '  ' in address:
               address = address.replace('  ', ' ')
          
          if '.' in address: address = address.replace('.', '')

          tags = {'building': True}
          
          a1 = address
          try:
               coords_list = address2coords(address)
               geometries = list2geom(coords_list)
               if geometries is not None: 
                    print(f"Сделано {address}")
                    return geometries
          except:    
               if 'улица' not in address:
                    if 'ул.' in address:
                         address.replace('ул.', 'улица')
                    elif 'ул' in address:
                         address.replace('ул', 'улица.')
               
               if '/' in address and 'стр' not in address_orig and 'кор' not in address_orig:
                    split_address = address.split(', ') if ', ' in address else address.split(',')
                    number = split_address[-1].split('/')
                    split_address[-1] = f"{number[1]}/{number[0]}"
                    address = ', '.join(split_address)
               
               if ' /' in address: address.replace(' /', '/')
               if '/ ' in address: address.replace('/' , '/')
               
               # elif '/' in address and 'стр' in address_orig:
               #      address_list = address.split('с ')
               #      address = address_list[0]
               #      split_address = address.split(', ') if ', ' in address else address.split(',')
               #      number = split_address[-1].split('/')
               #      split_address[-1] = f"{number[1]}/{number[1]}"
               #      address = ', '.join(split_address) + f'с {address_list[1]}'
                    
               if 'вал' in address and ' улица' in address:
                    address = address.replace(' улица', '')
                    address = f"улица {address}"
                    address = address.replace('  ', ' ')
               elif 'к ' in address:
                    address = address.replace('к ', 'к')
               elif 'с ' in address:
                    address = address.replace('с ', 'с')
               
               adjective_list = ['Большой', 'Малый', 'Большая', 'Малая', 'Старая', 'Новая', 'Старый', 'Новый']
               
               for adjective in adjective_list:
                    if adjective in address:
                         street = address.split(',')[0]
                         address = address.replace(f'{street}, ','')
                         street = street.replace(adjective, '')
                         address = f"{adjective} {street}, {address}"
                         break
               
               while '  ' in address:
                    address = address.replace('  ', ' ')
               a2 = address
               try:
                    coords_list = address2coords(address)
                    geometries = list2geom(coords_list)
                    if geometries is not None: 
                         print(f"Сделано {address}")
                         return geometries
               except:
                    '''

                    '''
                    if ' к' in address: address = address.replace(' к', 'к')
                    if ' с' in address: address = address.replace(' с', 'с')
                    
                    try:
                         int(address[-1])
                    except:
                         address = address.replace(address[-1], '')
                    
                    while '  ' in address:
                         address = address.replace('  ', ' ')
                    a3 = address
                    try:
                         coords_list = address2coords(address)
                         geometries = list2geom(coords_list)
                         if geometries is not None: return geometries
                    except Exception as e:
                         print(f"\n-------\nПроблемы со зданием: {address},\n\tоригинал: {address_orig},\n\tошибка:{e}\n\t1 итерация: {a1}\n\t1 итерация: {a2}\n\t1 итерация: {a3}\n-------\n")
                         with open(exceptions_file, 'a', encoding='UTF-8') as file:
                              file.write(f'{address_orig}, {type}\n, 1 итерация: {a1}\n2 итерация: {a2}\n3 итерация: {a3}\n\n')

for index, row in df.iterrows():
     address_original = row['Границы участка']
     uik_addr = row['УИК']
     voting_room_addr = row['Помещение для голосования']
     
     if 'дома' in address_original:
          address_original = address_original.replace('дома', 'дом')

     geometries = address_parse(address_original, exceptions_file, 'Границы участка')
     
     uchastok_addr = row['Номер участка']
     if pd.isna(uchastok_addr):
          if previous_uchastok is not None:
               uchastok_addr = previous_uchastok 
               
     if pd.isna(uik_addr):
          if previous_uik is not None:
               uik_addr = previous_uik
     else:
          uik_addr_coords = address_parse(uik_addr, exceptions_file, 'УИК')
     
     if pd.isna(voting_room_addr):
          if previous_voting_room is not None:
               voting_room_addr = previous_voting_room
     else:
          voting_room_addr_coords = address_parse(voting_room_addr, exceptions_file, 'Помещение для голосования')
          
     previous_uchastok = uchastok_addr 
     previous_uik = uik_addr
     previous_voting_room = voting_room_addr
     
     if geometries is not None:
          # geometries = address_coords['geometry']
          
          # geometry = unary_union(geometries)
          geometry = geometries
          # geometry = address_coords['geometry'].iloc[0]  # Берем первую геометрию
          list_geodata = [int(uchastok_addr), address_original, uik_addr, voting_room_addr, geometry]
          lists_geodata.append(list_geodata)
     else:
          continue
     
     if uik_addr_coords is not None:
          # geometry = uik_addr_coords['geometry'].iloc[0]
          # list_uik = [int(uchastok_addr), uik_addr, uik_addr_coords['geometry']]
          list_uik = [int(uchastok_addr), uik_addr, uik_addr_coords]
          lists_uik.append(list_uik)
     else:
          previous_uik = uik_addr
          continue
     
     if voting_room_addr_coords is not None:
          # geometry = voting_room_addr_coords['geometry'].iloc[0]
          # list_voting_room = [int(uchastok_addr), voting_room_addr, voting_room_addr_coords['geometry']]
          list_voting_room = [int(uchastok_addr), voting_room_addr, voting_room_addr_coords]
          lists_voting_room.append(list_voting_room)
     else:
          previous_voting_room = voting_room_addr
          continue
     
     # previous_uchastok = uchastok_addr 
     # previous_uik = uik_addr
     # previous_voting_room = voting_room_addr


gdf = gpd.GeoDataFrame(lists_geodata, columns=['Номер участка', 'Границы участка', 'УИК', 'Помещение для голосования', 'geometry'])
gdf = gdf.set_geometry('geometry')
gdf.to_file('geodata.gpkg', driver="GPKG")


temp_uik = []
for list_uik in lists_uik:
     if list_uik not in temp_uik:
          temp_uik.append(list_uik)
lists_uik = temp_uik

uik_gdf = gpd.GeoDataFrame(lists_uik, columns=['Номер участка', 'Номер УИК', 'geometry'])
uik_gdf = uik_gdf.set_geometry('geometry')
uik_gdf.to_file('uik.gpkg', driver="GPKG")


temp_voting_room= []
for list_voting_room in lists_voting_room:
     if list_voting_room not in temp_voting_room:
          temp_voting_room.append(list_voting_room)
lists_voting_room = temp_voting_room

voting_room_gdf = gpd.GeoDataFrame(lists_voting_room, columns=['Номер участка', 'Помещения для голосования', 'geometry'])
uik_gdf = uik_gdf.set_geometry('geometry')
voting_room_gdf.to_file('voting_room.gpkg', driver="GPKG")


with open(exceptions_file, 'r') as file:
     lines = file.readlines()

uniq_lines = set(lines)
with open(exceptions_file, 'w') as file:
     file.writelines(uniq_lines)
