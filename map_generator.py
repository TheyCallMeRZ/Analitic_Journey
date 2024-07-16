import requests
import matplotlib.pyplot as plt
from shapely import wkt,wkb
from shapely.geometry import Polygon
from shapely.ops import transform,unary_union
import pyproj
import pyodbc
import psycopg2
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
import folium
from folium import plugins as plugins
from folium.plugins import TagFilterButton
import json
from shapely.geometry import Polygon, mapping
import tkinter as tk
from tkinter import messagebox, filedialog
import webbrowser
import os
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import numpy as np
import time
from geopy.geocoders import Nominatim
# Zmienne stylu
tooltip_html = """
            <div style="
                width: 100px;
                text-align: center;
                font-size: 20px;
                font-family: Arial, sans-serif;
                color: black;
                text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
                background-color: transparent;
                border: none;
                box-shadow: none;
                padding: 0;
                margin: 0;
            ">
                <strong>{dist} km</strong>
            </div>
            """
catch_html ="""
    <div style="
        background-color: white;
        border: 2px solid black;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 3px 3px 5px grey;
    ">
        <strong>Populacja wg. spisu:</strong> {grid_pop}<br>
        <strong>Populacja wg. danych mobilnych:</strong> {hex_pop}<br>
        <strong>Średnia populacja:</strong> {avg_pop}
    </div>"""
shops_html =""" <div id="custom-marker" style="
        width: 100px;
        position: relative;
        top: -15px;
        left: -45px;
        text-align: center;
        font-size: 12px;
        font-family: Arial, sans-serif;
        color: black;
        text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff, -1px 1px 0 #fff, 1px 1px 0 #fff;
        background-color: transparent;
        border: none;
        box-shadow: none;
        padding: 0;
        margin: 0;
    ">
        <strong>{nazwa}</strong>
    </div>
"""
ross_html =""" <div id="custom-marker" style="
        width: 100px;
        position: relative;
        top: -57px;
        left: -45px;
        text-align: center;
        font-size: 20px;
        font-family: Arial, sans-serif;
        color: white;
        text-shadow: -1px -1px 0 darkred, 1px -1px 0 darkred, -1px 1px 0 darkred, 1px 1px 0 darkred;
        background-color: none;
        border: none;
        box-shadow: none;
        padding: 0;
        margin: 0;
    ">
        <strong>{nazwa}</strong>
    </div>
"""

def display_on_map():
    start_lat = float(entry_lat.get() or 0)  # Default to 0 if empty
    start_lon = float(entry_lon.get() or 0)  # Default to 0 if empty
    name = entry_name.get() or "map"  # Default to "map" if empty
    folder = entry_folder.get() or os.getcwd()
    bool_izoh = check_izoh.get()  # Default to 0 if empty
    bool_satelite = check_satelite.get()
    bool_hex = check_hex.get()
    bool_teren=check_teren.get()
    start_lon = float(entry_lon.get() or 0)  # Default to 0 if empty
    name = entry_name.get() or "map"  # Default to "map" if empty
    folder = entry_folder.get() or os.getcwd()
    radius = radius_var.get()
    ross_numb = numbsklepy_var.get()
    distsklepy = distsklepy_var.get()
    
    def get_sklepy(lat,lon,ross_numb):
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        query =f"""SELECT *,
                ST_Distance('SRID=4326;POINT({lon} {lat} )'::GEOGRAPHY, st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitiude" as real)),4326)::GEOGRAPHY,true)/1000 as dist,
                st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitiude" as real)),4326) as geom,
                st_makeline( 'SRID=4326;POINT({lon} {lat} )', st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitiude" as real)),4326)) as line 
                from shops_database 
                where "DateCloseShop" is  NULL or "DateCloseShop">Now()
                order by dist asc 
                limit {ross_numb}"""
        cur.execute(query)    
        columns =[column[0] for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.close()
        conn.close()
        df['point_geom'] = df['geom'].apply(wkb.loads)
        df['line_geom'] = df['line'].apply(wkb.loads)
        return df

    def get_shops(lat,lon,radius):
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        query =f"""SELECT*,
                ST_Distance('SRID=4326;POINT({lon} {lat})'::GEOGRAPHY, st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitude"as real)),4326)::GEOGRAPHY,true)/1000 as dist,
                st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitude"as real)),4326) as geom
                from baza_sklepow
                where ST_Distance('SRID=4326;POINT({lon} {lat})'::GEOGRAPHY,st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitude"as real)),4326)::GEOGRAPHY,true)/1000<{radius} 
                and "Type" in ('Supermarket','Dyskont','Drogeria','drogeria','Spożywczy','Hipermarket')
                and "ClosingDate">NOW()
                and "StoreName" != 'sklepy' and "StoreName"  in ('')
                order by dist asc
                """
        cur.execute(query)    
        columns =[column[0] for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.close()
        conn.close()
        df['point_geom'] = df['geom'].apply(wkb.loads)
        return df

    def calc_catch(lat,lon):
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        query = f"""WITH catchement AS (WITH nearest AS (
                SELECT 
                    text("ShopId") AS shop_id, 
                    ST_SetSRID(ST_MakePoint(CAST("Longitude" AS real), CAST("Latitiude" AS real)), 4326) AS geom,
                    ST_Distance( 
                        'SRID=4326;POINT({lon} {lat})'::GEOGRAPHY, 
                        ST_SetSRID(ST_MakePoint(CAST("Longitude" AS real), CAST("Latitiude" AS real)), 4326)::GEOGRAPHY, true
                    ) / 1000 AS dist
                FROM shops_database
                ORDER BY dist ASC
                LIMIT 30
            ), proposed AS (
                SELECT 
                    'Proponowana' AS shop_id,
                    'SRID=4326;POINT({lon} {lat})'::GEOMETRY AS geom
            )
            , combined AS (
                SELECT shop_id, geom FROM nearest
                UNION ALL
                SELECT * FROM proposed
            ), voronoi AS (
                SELECT 
                    (ST_DUMP(ST_VoronoiPolygons(ST_Collect(geom::geometry)))).geom AS voronoi_geom
                FROM combined
            )
            SELECT 
                combined.shop_id,
                ST_INTERSECTION(ST_BUFFER('SRID=4326;POINT({lon} {lat})'::GEOMETRY,0.1)/*Tutaj zmień dystans*/,voronoi.voronoi_geom) as voronoi_geom
            FROM 
                combined,
                voronoi
            WHERE 
                ST_Intersects(combined.geom,voronoi.voronoi_geom) AND shop_id='Proponowana')
            SELECT catchement.shop_id, sum("2021_pop_") AS grid_pop, t1.pop AS hex_pop, catchement.voronoi_geom AS geom
            FROM catchement 
            JOIN databank.grid_2021 AS grid ON ST_Intersects(catchement.voronoi_geom, grid.geom) 
            JOIN (SELECT shop_id, sum("hh03_n") AS pop, voronoi_geom AS geom
                FROM catchement 
                JOIN hexagons_database AS grid ON ST_Intersects(catchement.voronoi_geom, ST_Transform(grid.geom, 4326))
                GROUP BY shop_id, voronoi_geom) AS t1 ON catchement.shop_id = t1.shop_id
            GROUP BY catchement.shop_id, voronoi_geom, t1.pop;
            """
        cur.execute(query)    
        columns =[column[0] for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.close()
        conn.close()
        df['catch_geom'] = df['geom'].apply(wkb.loads)
        return df

    def get_hex(lat,lon):
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        query = f"""select *,st_transform(geom,4326) as geom_hex from databank.mobility_index_insta where st_dwithin(geom,st_transform(st_setsrid(st_makepoint({lon},{lat}),4326),3857),5000)
            """
        cur.execute(query)    
        columns =[column[0] for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.close()
        conn.close()
        df['hex_geom'] = df['geom_hex'].apply(wkb.loads)
        return df

    def get_city(lat,lon):
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        query = f"""with ross as (SELECT *,
                st_setsrid(ST_MakePoint(cast("Longitude" as real),cast("Latitiude" as real)),4326) as geom
            
                from shops_database 
            )
                select miasta.*,count(id) countsklepy  from databank.miasta LEFT JOIN ross on ST_within(ross.geom,miasta.geom)
                where st_within(st_setsrid(st_makepoint({lon} ,{lat}),4326),miasta.geom)
                group by id,miasta.geom,nazwa,area,pop
                """
        cur.execute(query)    
        columns =[column[0] for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.close()
        conn.close()
        df['city_geom'] = df['geom'].apply(wkb.loads)
        return df


    def get_isochrone(api_key, start_lat, start_lon, range_in_minutes):
        # Construct the request URL
        endpoint = "https://isoline.route.ls.hereapi.com/routing/7.2/calculateisoline.json"
        params = {
            'apiKey': api_key,
            'mode': 'fastest;car;traffic:enabled',
            'start': f'geo!{start_lat},{start_lon}',
            'range': range_in_minutes*60,
            'rangetype': 'time'
        }
        # Make the API request
        response = requests.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Define the function to plot the isochrone

    def create_polygon(response):
        
        shape_coordinates = response['response']['isoline'][0]['component'][0]['shape']
        coordinates = [(float(coord.split(',')[1]), float(coord.split(',')[0])) for coord in shape_coordinates]
        return Polygon(coordinates)

    try:
        # Create a folium map centered at the starting point
        db_params = {
            'host': 'host_name',
            'database': 'database_name',
            'user': 'user_name',
            'password': 'password_val'
            }
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])

        engine = create_engine(f"postgresql+psycopg2://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['database']}")
        dfsklepy=get_sklepy(start_lat,start_lon,ross_numb)
        df_catch = calc_catch(start_lat,start_lon)
        df_shops = get_shops(start_lat,start_lon,radius)
        df_hex = get_hex(start_lat,start_lon) 
        df_city = get_city(start_lat,start_lon)
       
        m = folium.Map(location=[start_lat, start_lon], zoom_start=12)
        # Strefy dojazdu
        if bool_izoh==1:
            try:
                polygons = []
                isochrones = []
                for range_in_minutes in ranges_in_minutes:
                    response = get_isochrone(api_key, start_lat,start_lon, range_in_minutes)
                    polygon = create_polygon(response)
                    polygons.append(polygon)

                    isochrones.append({
                        "name":name,
                        "lat":start_lat,
                        "lon":start_lon,
                        "range":range_in_minutes,
                        "geom":polygon.wkt
                    })

            except Exception as e:
                print('Isochrones')
                print(e)
            sum_query_template = """
                SELECT 
                    '{name1}' as isochrone_name,
                    SUM(mob.hh01_n) AS pop
                FROM 
                    hexagons_database mob
                WHERE 
                    ST_Within(st_transform(mob.geom,4326), ST_GeomFromText(%s, 4326));
                """
            df_isochrones = pd.DataFrame(isochrones)
            results = []
            cur = conn.cursor()
            for _,row in df_isochrones.iterrows():
                sum_query = sum_query_template.format(name1=row['name'])
                cur.execute(sum_query,(row['geom'],))
                result=cur.fetchone()
                results.append(result)
            cur.close()
            conn.close()

            df_results =pd.DataFrame(results, columns=['isochrone_name','pop'])
            table_name1 = 'isochrones_presentation'
            df_isochrones.to_sql(table_name1, engine, schema='databank',if_exists='append',index=False)
            #Add each polygon to the map with different colors
            colors = ['blue', 'green', 'red']
            strefy_fg = folium.FeatureGroup(name='Strefy dojazdu')
            for i, polygon in enumerate(polygons):
                geojson_str = json.dumps(mapping(polygon))
                folium.GeoJson(
                    geojson_str,
                    name=f"Strefa dojazdu {(3-i)*5}",
                    style_function=lambda x, color=colors[i]: {'color': color, 'weight': 2, 'fillOpacity': 0.3},
                    popup=folium.Popup(f"Czas dojazdu samochodem w ciągu:{(3-i)*5} min")
                ).add_to(strefy_fg)
            strefy_fg.add_to(m)

        # Google street
        folium.TileLayer(
            tiles='http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            max_zoom=20,
            subdomains=['mt0', 'mt1', 'mt2', 'mt3']
        ).add_to(m)
        # Google Satelite
        if bool_satelite==1:
            folium.TileLayer(
                    tiles='http://{s}.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}',
                    attr='Google',
                    name='Google Satelite',
                    max_zoom=20,
                    subdomains=['mt0', 'mt1', 'mt2', 'mt3'],
                    show=False
                ).add_to(m)
        

        plugins.Draw(draw_options={"rectangle":False,"circle":False,"circlemarker":False}).add_to(m)
        plugins.Geocoder(position='topleft',collapsed=True,add_marker=False).add_to(m)

        # Info box
        box_html= f"""
                    <div id="data-box" style="
                        position: fixed;
                        bottom: 20px;
                        right: 20px;
                        max-width: 600px;
                        background-color: #f9f9f9;
                        border: 2px solid #ccc;
                        border-radius: 10px;
                        z-index: 1000;
                        padding: 20px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        font-family: Arial, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                    ">
                        <h3 style="margin-bottom: 10px;"><strong>{name}</strong></h3>
                        <h4 style="margin-bottom: 5px;"><strong>Dane Catchementowe:</strong></h4>
                        <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Populacja miasta:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{'brak granic' if df_city.empty else df_city['pop'][0]}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Ilość sklepów sklepy w mieście:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{'brak granic' if df_city.empty else df_city['countsklepy'][0]}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Populacja per sklepy w mieście:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{'brak granic' if df_city.empty else int(round(df_city['pop'][0]/(df_city['countsklepy'][0]+1),0))}</td>
                            </tr>
                            <tr style="background-color: rgba(255, 0, 0, 0.1);"> 
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement strefa dojazdu 5 min:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(df_results['pop'][2]) if bool_izoh==1 else ""}</td>
                            </tr>
                            <tr style="background-color: rgba(0, 255, 0, 0.1);">
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement strefa dojazdu 10 min:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(df_results['pop'][1]) if bool_izoh==1 else ""}</td>
                            </tr>
                            <tr style="background-color: rgba(0, 0, 255, 0.1);">
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement strefa dojazdu 15 min:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(df_results['pop'][0]) if bool_izoh==1 else ""}</td>
                            </tr>
                            <tr style="background: linear-gradient(100deg, rgba(255, 0, 0, 0.1) 0% 33% , rgba(0, 255, 0, 0.1) 30% 66%, rgba(0, 0, 255, 0.1) 66%);">
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement behawioralny:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(int(df_results['pop'][0])*0.6+(int(df_results['pop'][1])-int(df_results['pop'][0]))*0.3+(int(df_results['pop'][2])-int(df_results['pop'][1]))*0.1) if bool_izoh==1 else ""}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement według spisu:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(df_catch['grid_pop'][0])}</td>
                            </tr>
                            
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement według danych mobilnych:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{df_catch['hex_pop'][0]}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Catchement średni (spis i mobilne):</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{int(round((float(df_catch['grid_pop'][0])+float(df_catch['hex_pop'][0]))/2,0))}</td>
                            </tr>
                        </table>
                        <h4 style="margin-bottom: 5px;"><strong>Dane konkurenckie:</strong></h4>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Ilość sklepów spożywczych w promieniu 2 km:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{((df_shops['dist']<=2)&(df_shops["Type"].isin(['Supermarket','Dyskont','Spożywczy','Hipermarket']))).sum()}</td>
                            </tr>
                            <tr>
                                <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold;">Ilość sklepów konkurenckich w promieniu 2 km:</td>
                                <td style="border: 1px solid #ddd; padding: 10px;">{((df_shops['dist']<=2)&(df_shops["Type"].isin(['Drogeria','drogeria']))).sum()}</td>
                            </tr>
                        </table>
                    </div>
                        </div>
                        <style>
                        @media (max-width: 480px){{
                            #data-box {{
                                max-width: 10%;
                                max-height: 100%;
                                bottom: 2px;
                                right: 2px;
                                padding: 1px;
                            }}

                            #data-box h3, #data-box h4 {{
                                font-size: 7px;
                            }}

                            #data-box td {{
                                padding: 2px;
                                font-size: 6px;
                            }}
                        }}
                    </style>
                    <script>
                        function toggleOpacity() {{
                            var dataBox = document.getElementById('data-box');
                            var currentOpacity = window.getComputedStyle(dataBox).opacity;
                            dataBox.style.opacity = (currentOpacity == 1) ? 0 : 1;
                            dataBox.style.pointerEvents = (currentOpacity == 1) ? 'none' : 'auto';
                            }}
                    </script>
                        """
        button_html = """
                    <div style="
                        position: fixed;
                        bottom: 10px;
                        left: 10px;
                        z-index: 1000;
                    ">
                        <button onclick="toggleOpacity()" style="
                            padding: 10px 20px;
                            background-color: #007bff;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                        ">Pokaż/ukryj tabelę wyliczeń</button>
                    </div>
                    """
        m.get_root().html.add_child(folium.Element(box_html+button_html))

    # Hexagons
        if bool_hex==1:
            hex_fg = folium.FeatureGroup(name='Hexagony',show=False)
            column_names = [f'hh{i:02d}_insta' for i in range(24)]
            for _, row in df_hex.iterrows():
                folium.GeoJson(
                    data=row['hex_geom'],
                    name='Hex',
                    style_function=lambda feature,row=row: {
                        'fillColor': '#64FF33' if row[column_names[14]] < 100 else '#D00000' if row[column_names[14]] > 500 else '#FFEC33',
                        'color': '#64FF33' if row[column_names[14]] < 100 else '#D00000' if row[column_names[14]] > 500 else '#FFEC33',
                        'weight': 2,
                        'fillOpacity': 0.4
                    },
                    tooltip=f'Populacja o godzinie {column_names[14]}: {row[column_names[14]]}'
                ).add_to(hex_fg)
            hex_fg.add_to(m)
        

        # Miasta
        for _, row in df_city.iterrows():
            folium.GeoJson(
                name='Miasto',
                data=row['city_geom'],
                style_function=lambda feature: {
                    'fill': False,
                    'color': '#004DFF',
                    'weight': 4,
                    'fillOpacity': 0.4
                }
            ).add_to(m)
        

        # Catchement
        for _, row in df_catch.iterrows():
            folium.GeoJson(
                name='Catchement',
                
                data=row['catch_geom'],
                style_function=lambda feature: {
                    'fillColor': 'gray',
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': 0.4
                },
                tooltip=folium.Tooltip(catch_html.format(grid_pop=float(row['grid_pop']),hex_pop=float(row['hex_pop']),avg_pop=(float(row['grid_pop'])+float(row['hex_pop']))/2))
                ,show=False
            ).add_to(m)
        

        # Sklepy inne
        nazwy_sklepow = df_shops['StoreName'].unique().tolist()
        TagFilterButton(nazwy_sklepow).add_to(m)
        shops_fg = folium.FeatureGroup(name='Sklepy',show=False)
        etykiety_fg = folium.FeatureGroup(name='Etykiety',show=False)
        for _, row in df_shops.iterrows():
            point = row['point_geom']
            shopid =row['StoreName']
            folium.Marker(
                location=[point.y, point.x],
                popup=f'Baner: {shopid}',
                tags=[shopid],
                icon=plugins.BeautifyIcon(border_color='purple',icon_shape="circle-dot",border_width=5)
            ).add_to(shops_fg)
            folium.Marker(
                location=[point.y, point.x],
                tags=[shopid],
                icon= folium.DivIcon(
                    html=shops_html.format(nazwa=shopid))   
                ).add_to(etykiety_fg)
        etykiety_fg.add_to(m)
        shops_fg.add_to(m)
        

        
    
        etykietyross_fg = folium.FeatureGroup(name='Etykiety sklepy',show=True)
        sklepy_fg = folium.FeatureGroup(name='sklepy')
        for _, row in dfsklepy.iterrows():
            point = row['point_geom']
            shopid =row['ShopId']
            folium.Marker(
                location=[point.y, point.x],
                popup=f'Numer sklepu: {shopid}',
                icon=folium.Icon(color='darkred', icon='home')
            ).add_to(sklepy_fg)
            folium.Marker(
                location=[point.y, point.x],
                tags=[shopid],
                icon= folium.DivIcon(
                    html=ross_html.format(nazwa=shopid))   
                ).add_to(etykietyross_fg)
        sklepy_fg.add_to(m)
        etykietyross_fg.add_to(m)
        # Odległości od sklepy
        lines_fg = folium.FeatureGroup(name='Odległości od sklepy',show=False)
        for _, row in dfsklepy.head(distsklepy).iterrows():
            line = row['line_geom']
            dist =row['dist']
            folium.GeoJson(
            data=line,
            #tooltip=folium.Tooltip(tooltip_html.format(dist=round(dist, 2)),permanent=True),
            style_function=lambda x: {'color': 'black', 'weight': 3,'dashArray': '5, 10'}
            ).add_to(lines_fg)
            midpoint = line.interpolate(0.5,normalized=True)
            folium.Marker( location=[midpoint.y, midpoint.x],
            icon=folium.DivIcon(
                html=tooltip_html.format(dist=round(dist, 2))
                )   
            ).add_to(lines_fg)
        lines_fg.add_to(m)
        

        # punkt startu
        folium.Marker(
            location=[start_lat, start_lon],
            popup=f"Rozpatrywana lokalizacja: {name}",
            icon=folium.Icon(icon='info-sign')
        ).add_to(m)
        

        # StreetView part
        gugl = """
            $ (document).ready(function (e) {
            var new_mark = L.marker();
            function newMarker(e){
            new_mark.setLatLng(e.latlng).addTo(map1);
            new_mark.setZIndexOffset(-1);
            new_mark.on('dblclick', function(e){
            (map1).removeLayer(e.target)})
            var lat = e.latlng.lat.toFixed(4),
            lng = e.latlng.lng.toFixed(4);
            new_mark.bindPopup(
            "<a href=https://www.google.com/maps?layer=c&cbll=" + lat + "," + lng + " target=blank><img  width=70 alt= Streetviewclass=StreetViewImage></img></a>",{
            maxWidth: "auto",
            className: 'StreetViewPopup'
            });
            };
            (map1).on('click', newMarker); 
            });
            """.replace("map1",str('map_'+m._id))
        m.get_root().script.add_child(folium.Element(gugl))

        # Zagospodarowanie terenu
        if bool_teren ==1:
            folium.WmsTileLayer(url='https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow',layers='dzialki,numery_dzialek,budynki',name='Zagospodarowanie terenu',fmt="image/png",transparent=True).add_to(m)
        # Add layer control
        folium.LayerControl().add_to(m)
        logged_user = os.getlogin()
        # Export to postgresql
        if df_city.empty:
            df_export = pd.DataFrame({
                    'name':[name],
                    "city": ['Brak granic'],
                    "pop_city":[0],
                    "":[0],
                    'catch_grid':[df_catch['grid_pop'][0]],
                    'catch_hex':[df_catch['hex_pop'][0]],
                    'count_rival_2km':[((df_shops['dist']<=2)&(df_shops["Type"].isin(['Drogeria','drogeria']))).sum()],
                    'count_food_2km':[((df_shops['dist']<=2)&(df_shops["Type"].isin(['Supermarket','Dysont','Spożywczy','Hipermarket']))).sum()],
                    'lat':[start_lat],
                    'lon':[start_lon],
                    "catch_geom":[df_catch['geom'][0]],
                    "creator":logged_user
                })
        else:
            df_export = pd.DataFrame({
                'name':[name],
                "city": [df_city['nazwa'][0]],
                "pop_city":[df_city['pop'][0]],
                "countsklepy_city":[df_city['countsklepy'][0]],
                'catch_grid':[df_catch['grid_pop'][0]],
                'catch_hex':[df_catch['hex_pop'][0]],
                'count_rival_2km':[((df_shops['dist']<=2)&(df_shops["Type"].isin(['Drogeria','drogeria']))).sum()],
                'count_food_2km':[((df_shops['dist']<=2)&(df_shops["Type"].isin(['Supermarket','Dysont','Spożywczy','Hipermarket']))).sum()],
                'lat':[start_lat],
                'lon':[start_lon],
                "catch_geom":[df_catch['geom'][0]],
                "creator":logged_user
            })
        map_filename = os.path.join(folder, f"{name}.html")
        m.save(map_filename)
        # Open map
        webbrowser.open(f"file://{os.path.abspath(map_filename)}")
        table_name = 'presentation_data'
        df_export.to_sql(table_name, engine, schema='databank',if_exists='append',index=False)
        messagebox.showinfo("Powodzenie", f"Mapa o nazwie: {name} , została wygenerowana.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e} {e.with_traceback} {e.__context__}")
    
def get_plots():
    start_lat1 = float(entry_lat.get() or 0)# Default to 0 if empty
    start_lon1= float(entry_lon.get() or 0) # Default to 0 if empty
    name1 = entry_name.get() or "map"  # Default to "map" if empty
    folder1 = entry_folder.get() or os.getcwd()
    def traffic_plot(y,x,x1,name,title):
        quant = np.quantile(x,[0.33,0.67])
        def get_color(value, quantiles):
            if value <= quantiles[0]:
                return 'red'
            elif value <= quantiles[1]:
                return 'orange'
            else:
                return 'green'
        profit_color = [get_color(p,quant) for p in x]
        #plt.figure(figsize=(12,6))
        fig,ax = plt.subplots()
        bars = ax.bar(y,x,color=profit_color)
        bars1 =  ax.bar(y,x1,color='black',alpha=0.4)
        fig.set_size_inches(15.5,7.5)
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2,yval+1,round(yval,2),ha = 'center', va= 'bottom')
        fig.suptitle(title)
        ax.set_title(f"Najlepsza godzina: {x.index(max(x))}       Najgorsza godzina: {x.index(min(x))}       Suma ludzi w godz. 8-22: {sum(x[8:23])}" )
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#DDDDDD')
        ax.tick_params(bottom=False, left=False)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color='#EEEEEE')
        ax.xaxis.grid(False)
        ax.set_xlabel("Godziny")
        ax.set_ylabel("Ilość ludzi")
        fig.tight_layout()
        plot_name = os.path.join(folder1, f"{name}.png")
        plt.savefig(plot_name)
        #plt.show()

    def traffic_1(lon,lat,name):
        title = 'Pojedynczy Hexagon'
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        cur.execute(f"select * from databank.mobility_index_insta where st_contains(geom,st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857))")
        columns =[column[0].replace("hh","").replace("_insta",'') for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        y= columns[7:31]
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.execute(f"""select * from hexagons_database where st_contains(geom,st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857))""")
        columns1 =[column[0].replace("hh","").replace("n",'') for column in cur.description]
        # Fetch all rows
        rows1 = cur.fetchall()
        y1= columns1[7:31]
        data1=[tuple(row) for row in rows1]
        df1 = pd.DataFrame(data1,columns=columns1)
        cur.close()
        conn.close()    
        val=df.iloc[:,7:31].sum().astype(int)
        val_list = val.tolist()
        val1=df1.iloc[:,7:31].sum().astype(int)
        val_list1 = val1.tolist()
        # Wykres
        traffic_plot(y,val_list,val_list1,f'{name}_1',title)
    
    def traffic_3(lon,lat,name):
        title = 'Okoliczne Hexagony'
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        cur.execute(f"""with selected_hex as (select geom from databank.mobility_index_insta where st_contains(geom,st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857))) select a.* from databank.mobility_index_insta as a, selected_hex as b where ST_Touches(a.geom,b.geom) or ST_equals(a.geom,b.geom)""")
        columns =[column[0].replace("hh","").replace("_insta",'') for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        y= columns[7:31]
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.execute(f"with selected_hex as (select geom from hexagons_database where st_contains(geom,st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857))) select a.* from hexagons_database as a, selected_hex as b where ST_Touches(a.geom,b.geom) or ST_equals(a.geom,b.geom)")
        columns1 =[column[0].replace("hh","").replace("_n",'') for column in cur.description]
        # Fetch all rows
        rows1 = cur.fetchall()
        y1= columns1[7:31]
        data1=[tuple(row) for row in rows1]
        df1 = pd.DataFrame(data1,columns=columns1)
        cur.close()
        conn.close()
        val=df.iloc[:,7:31].sum().astype(int)
        val_list = val.tolist()
        val1=df1.iloc[:,7:31].sum().astype(int)
        val_list1 = val1.tolist()
        # Wykres
        traffic_plot(y,val_list,val_list1,f'{name}_3',title)
        
    def traffic_2(lon,lat,name):
        title = 'Najbliższe 3 Hexagony'
        db_params = {
            'host':'host_name',
            'database':'database_name',
            'user':'user_name',
            'password':'password_val'
                    }
        engine = create_engine(f'postgresql://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}/{db_params["database"]}',connect_args={'connect_timeout':200})
        conn = psycopg2.connect(host=db_params['host'],database=db_params['database'],user=db_params['user'],password=db_params['password'])
        cur = conn.cursor()
        cur.execute(f"""select * from databank.mobility_index_insta where st_intersects(geom,st_buffer(st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857),87))""")
        columns =[column[0].replace("hh","").replace("_insta",'') for column in cur.description]
        # Fetch all rows
        rows = cur.fetchall()
        y= columns[7:31]
        data=[tuple(row) for row in rows]
        df = pd.DataFrame(data,columns=columns)
        cur.execute(f"select * from hexagons_database where st_intersects(geom,st_buffer(st_transform(st_setsrid(st_makepoint({lat},{lon}),4326),3857),87))")
        columns1 =[column[0].replace("hh","").replace("_n",'') for column in cur.description]
        # Fetch all rows
        rows1 = cur.fetchall()
        y1= columns1[7:31]
        data1=[tuple(row) for row in rows1]
        df1 = pd.DataFrame(data1,columns=columns1)
        cur.close()
        conn.close()
        val=df.iloc[:,7:31].sum().astype(int)
        val_list = val.tolist()
        val1=df1.iloc[:,7:31].sum().astype(int)
        val_list1 = val1.tolist()
        # Wykres
        traffic_plot(y,val_list,val_list1,f'{name}_2',title)
        
    def traffic(lon,lat,name):
        traffic_1(lon,lat,name)
        traffic_2(lon,lat,name)
        traffic_3(lon,lat,name)
    
    try:
        pass
        traffic_1(start_lat1,start_lon1,name1)
        traffic_2(start_lat1,start_lon1,name1)
        traffic_3(start_lat1,start_lon1,name1)
        messagebox.showinfo("Powodzenie", f"Wykresy o nazwie: {name1} , zostały wygenerowana.")
        

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
    
# Define your HERE API key
api_key = 'key'
def select_folder():
    folder_selected = filedialog.askdirectory()
    entry_folder.delete(0, tk.END)
    entry_folder.insert(0, folder_selected)
# Define start coordinates and range
def create_label_entry(root, label_text, entry_var, row):
    label = tk.Label(root, text=label_text, bg="#f0f0f0", font=("Arial", 10))
    label.grid(row=row, column=0, padx=10, pady=5, sticky="w")
    entry = tk.Entry(root, textvariable=entry_var, font=("Arial", 10))
    entry.grid(row=row, column=1, padx=10, pady=5, sticky="ew")
    return entry

ranges_in_minutes = [15,10,5]
def geocode_address():
    address = address_var.get()
    geolocator = Nominatim(user_agent="mapgeneratortest")
    
    try:
        location = geolocator.geocode(address)
        if location:
            lat_var.set(location.latitude)
            lon_var.set(location.longitude)
        else:
            messagebox.showerror("Error", "Nie znaleziono adresu")
    except Exception as e:
        messagebox.showerror("Error", f"Geocoding failed: {e}")

root = tk.Tk()
root.title("Generator mapy")
root.configure(bg="#f0f0f0")
root.geometry("700x600")
lat_var = tk.StringVar()
lon_var = tk.StringVar()
name_var = tk.StringVar()
address_var = tk.StringVar()
folder_var = tk.StringVar()
check_hex = tk.IntVar()
check_satelite = tk.IntVar()
check_teren = tk.IntVar()
check_izoh = tk.IntVar()
radius_var = tk.IntVar() 
numbsklepy_var = tk.IntVar()
distsklepy_var = tk.IntVar()

# Latitude inputw
entry_lat = create_label_entry(root, "Szerokość geograficzna (większe wartości):", lat_var, 0)

# Longitude input
entry_lon = create_label_entry(root, "Długość geograficzna (mniejsze wartości):", lon_var, 1)

# Address input
entry_address = create_label_entry(root, "Wprowadź adres: ", address_var, 2)

# Geocode button
geocode_button = tk.Button(root, text="Znajdź współrzędne", command=geocode_address, font=("Arial", 10), bg="#4caf50", fg="white")
geocode_button.grid(row=2, column=2, padx=10, pady=5, sticky="ew")

# Map name input
entry_name = create_label_entry(root, "Nazwa mapy:", name_var, 3)

# Save folder input
entry_folder = create_label_entry(root, "Folder do zapisania:", folder_var, 4)

# Folder selection button
folder_button = tk.Button(root, text="Wybierz folder do zapisania", command=select_folder, font=("Arial", 10), bg="#4caf50", fg="white")
folder_button.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

# Parameters specification
numbsklepy_var.set(15)
numbsklepy_label = tk.Label(root, text="Ilość najbliższych sklepyów ", bg="#f0f0f0", font=("Arial", 10))
numbsklepy_label.grid(row=6, column=0, padx=10, pady=5, sticky="w")
entry_numbsklepy = tk.Entry(root, textvariable=numbsklepy_var, font=("Arial", 10))
entry_numbsklepy.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

distsklepy_var.set(5)
distsklepy_label = tk.Label(root, text="Ilość linii do najbliższych sklepyów: ", bg="#f0f0f0", font=("Arial", 10))
distsklepy_label.grid(row=7, column=0, padx=10, pady=5, sticky="w")
entry_distsklepy = tk.Entry(root, textvariable=distsklepy_var, font=("Arial", 10))
entry_distsklepy.grid(row=7, column=1, padx=10, pady=5, sticky="ew")

radius_var.set(5)
radius_label = tk.Label(root, text="Sklepy w promieniu (w kilometrach): ", bg="#f0f0f0", font=("Arial", 10))
radius_label.grid(row=8, column=0, padx=10, pady=5, sticky="w")
entry_radius = tk.Entry(root, textvariable=radius_var, font=("Arial", 10))
entry_radius.grid(row=8, column=1, padx=10, pady=5, sticky="ew")

# Check boxes
checkbox1 = tk.Checkbutton(root, text='Hexagony', variable=check_hex, onvalue=1, offvalue=0)
checkbox1.select()
checkbox1.grid(row=9, column=0, columnspan=1, padx=1, pady=1, sticky="W")
checkbox2 = tk.Checkbutton(root, text='Widok satelitarny', variable=check_satelite, onvalue=1, offvalue=0)
checkbox2.select()
checkbox2.grid(row=9, column=1, columnspan=1, padx=1, pady=1, sticky="W")
checkbox3 = tk.Checkbutton(root, text='Zagospodarowanie terenu', variable=check_teren, onvalue=1, offvalue=0)
checkbox3.select()
checkbox3.grid(row=10, column=0, columnspan=1, padx=1, pady=1, sticky="W")
checkbox4 = tk.Checkbutton(root, text='Strefy dojazdu', variable=check_izoh, onvalue=1, offvalue=0)
checkbox4.select()
checkbox4.grid(row=10, column=1, columnspan=1, padx=1, pady=1, sticky="W")

# Generate map button
generate_button = tk.Button(root, text="Generuj mapę", command=display_on_map, font=("Arial", 10), bg="#4caf50", fg="white")
generate_button.grid(row=11, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

# Get plots button
generate_button = tk.Button(root, text="Generuj wykresy", command=get_plots, font=("Arial", 10), bg="#4caf50", fg="white")
generate_button.grid(row=12, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

root.columnconfigure(1, weight=1)

# Run the application
root.mainloop()
