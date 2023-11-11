import pandas as pd
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point

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


def address_parse(address, exceptions_file, type):
     address_orig = address
     address = address.replace('дом №', '')
     
     if '-ый' in address: address = address.replace('-ый', '-й')
     if '-ой' in address: address = address.replace('-ой', '-й')
     if '-ий' in address: address = address.replace('-ий', '-й')
     
     if '_x0002_' in address: address = address.replace('_x0002_', '-')
     
     if '(корп' in address:
          address_list = address.split('(корп')
          address = f"{address_list[0]}к{address_list[1]}".replace(')', '')
     if '(стр.' in address:
          address_list = address.split('(стр.')
          address = f"{address_list[0]}с{address_list[1]}".replace(')', '')
     if '(кор' in address:
          address_list = address.split('(кор')
          address = f"{address_list[0]}к{address_list[1]}".replace(')', '')
     
     while '  ' in address:
          address = address.replace('  ', ' ')
     
     if '.' in address: address = address.replace('.', '')
     
     try:
          location = ox.geocode(f'Москва, {address}')
          address_coords = Point(location[1], location[0])         
          return address_coords
     except Exception as e:
          if 'вал' in address and ' улица' in address:
               address = address.replace(' улица', '')
               address = f"улица {address}"
               address = address.replace('  ', ' ')
          elif 'к ' in address:
               address = address.replace('к ', 'к')
          elif 'с ' in address:
               address = address.replace('с ', 'с')   
               
          while '  ' in address:
               address = address.replace('  ', ' ')  
          
          try:
               location = ox.geocode(f'Москва, {address}')
               address_coords = Point(location[1], location[0])         
               return address_coords   
          except Exception as e:
               '''
               Ввиду возникновения большого количества исключений (100 штук) в код прописаны строки 72 и 73, которые, фактически, ищут здания не учитывая их строений и корпусов
               Метод менее точный, чем сделать всё по-умному, но работает
               '''
               if ' к' in address: address = address.split(' к')[0]
               if ' с' in address: address = address.split(' с')[0]
               
               while '  ' in address:
                    address = address.replace('  ', ' ')
               try:
                    location = ox.geocode(f'Москва, {address}')
                    address_coords = Point(location[1], location[0])         
                    return address_coords   
               except Exception as e:
                    print(f"Проблемы со зданием: {address},\n\tоригинал: {address_orig},\n\tошибка: {e}")
                    with open(exceptions_file, 'a') as file:
                         file.write(f'{address_orig}, {type}\n')

for index, row in df.iterrows():
     address_original = row['Границы участка']
     uik_addr = row['УИК']
     voting_room_addr = row['Помещение для голосования']
     
     if 'дома' in address_original:
          address_original = address_original.replace('дома', 'дом')
     
     address_coords = address_parse(address_original, exceptions_file, 'Границы участка')
     
     uchastok_addr = row['Номер участка']
     if pd.isna(uchastok_addr):
          if previous_uchastok is not None:
               uchastok_addr = previous_uchastok 
               
     if pd.isna(uik_addr):
          if previous_uik is not None:
               uik_addr = previous_uik
     uik_addr_coords = address_parse(uik_addr, exceptions_file, 'УИК')
     
     if pd.isna(voting_room_addr):
          if previous_voting_room is not None:
               voting_room_addr = previous_voting_room
     voting_room_addr_coords = address_parse(voting_room_addr, exceptions_file, 'Помещение для голосования')

     list_geodata = [int(uchastok_addr), address_original, uik_addr, voting_room_addr, address_coords]
     lists_geodata.append(list_geodata)
     
     list_uik = [int(uchastok_addr), uik_addr, uik_addr_coords]
     lists_uik.append(list_uik)
     
     list_voting_room = [int(uchastok_addr), voting_room_addr, voting_room_addr_coords]
     lists_voting_room.append(list_voting_room)
     
     previous_uchastok = uchastok_addr 
     previous_uik = uik_addr
     previous_voting_room = voting_room_addr


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
