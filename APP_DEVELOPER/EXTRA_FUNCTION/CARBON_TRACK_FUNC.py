import googlemaps
import numpy as np
import pandas as pd
import requests
import json

class CO2_Calculator:
    with open(r"C:\Users\wesley\Desktop\API_KEYS.json") as f:
        config = json.load(f)

    def __init__(self):
        self.gmaps = googlemaps.Client(key = config["GOOGLE_MAPS_API_KEY"])
        self.OUROWN_HOUSE = (23.492920860195206, 120.3796313899456)  # Starting location
        self.total_emission = 0
        self.log_path = r"Z:\\跨部門\\共用資料夾\\F. 管理部\\05.碳盤查資訊與資料\\2025年度碳盤資料\\活動數據\\類別三\\外車司機\\2025_CARTRACK_SUMMARY\\TRACK_LOG.txt"
        self.factory_data_path = r"Z:\\跨部門\\共用資料夾\\F. 管理部\\05.碳盤查資訊與資料\\FACTORY_COORDINATE.xlsx"
        self.image_save_path = r"Z:\\跨部門\\共用資料夾\\F. 管理部\\05.碳盤查資訊與資料\\2025年度碳盤資料\\活動數據\\類別三\\外車司機\\2025_CARTRACK_SUMMARY\\ORDER_ROUTE_PIC_2025"

    def ROUTE_CALCULATOR(self, waypoint_list, weight_list, order_name):
        self.total_emission = 0
        track = {}

        directions_result = self.gmaps.directions(
            origin=self.OUROWN_HOUSE,  # Start point
            destination=self.OUROWN_HOUSE,  # Return to start
            waypoints=waypoint_list,  # Waypoints to visit
            optimize_waypoints = False,  # Optimize for shortest path
            mode="driving"
        )

        self.DRAW_MAP(directions_result, order_name)  # Generate route image

        # Extract optimized route
        route = directions_result[0]['legs']
        optimized_order = directions_result[0]['waypoint_order']
        optimized_weight = np.cumsum(np.array([weight_list[i] for i in optimized_order] + [0])[::-1])[::-1]

        name = order_name.split("\\")[1]  # Extract order name
        track["ALL_ROUTE"] = []

        with open(self.log_path, "a", encoding="UTF-8") as log_file:
            log_file.write(f"\nOptimized route order: {name}")
            for i, leg in enumerate(route):
                start_address = leg['start_address']
                end_address = leg['end_address']
                distance = leg['distance']['value'] / 1000  # Convert meters to km
                duration = leg['duration']['text']
                co2_tons_km = distance * optimized_weight[i] / 1000  # Calculate CO2 emissions
                self.total_emission += co2_tons_km

                log_file.write(f"\n{i + 1}: {start_address} -> {end_address}, {distance} km, {duration}, Emission {co2_tons_km}")
                track["ALL_ROUTE"].append({
                    "START_POINT": start_address,
                    "END_POINT": end_address,
                    "DISTANCE": distance,
                    "EMISSION": co2_tons_km,
                    "WEIGHT": float(optimized_weight[i])
                })

            # Log total distance, emissions, and time
            total_distance = sum(leg['distance']['value'] for leg in route) / 1000
            total_duration = sum(leg['duration']['value'] for leg in route) / 60  # Convert seconds to minutes

            log_file.write(f"\nTotal distance: {total_distance:.3f} km")
            log_file.write(f"\nTotal Emission: {self.total_emission:.3f} Tons CO2e")
            log_file.write(f"\nTotal duration: {total_duration:.2f} minutes\n")

        track["TOTAL DISTANCE"] = total_distance
        track["TOTAL_EMISSION"] = self.total_emission
        track["TOTAL_TIME"] = duration

        return order_name, total_distance, self.total_emission, track

    def TRANS_ORDER_INTO_CO2(self, order_file):
        # Load factory coordinate data
        factory_data = pd.read_excel(self.factory_data_path)

        # Load order data
        order_number = pd.read_excel(order_file)
        order_list = order_number["FACTORY_CODE"].tolist()
        #print(order_number)

        # transdorm the weight in each trip into summary 2025/03/19 已請生管登記每日出發順序明年計算時請修改
        raw_list = order_number["KGS"].tolist()
        TOTAL_WEIGHT = sum(raw_list)
        weight_list = []

        for i in raw_list:
            weight_list.append(TOTAL_WEIGHT)
            TOTAL_WEIGHT -= int(i)

        weight_list.append(0)  # Last trip is empty

        #check if all the order is in the coordinate list
        for factory_code in order_list :
            if factory_code not in factory_data["FACTORY_CODE"].values :
                raise ValueError("{} please add this factory into the coordinate file".format(factory_code))

        # Get coordinates for each factory
        coordinate_list = [factory_data.loc[factory_data["FACTORY_CODE"] == item, "COORDINATE"].values[0] for item in order_list]

        return self.ROUTE_CALCULATOR(coordinate_list, weight_list, order_file.split(".")[0])

    def DRAW_MAP(self, direction_info, order):
        route = direction_info[0]['legs']
        waypoints_ordered = [route[i]['end_location'] for i in range(len(route))]

        base_url = "https://maps.googleapis.com/maps/api/staticmap?"
        encoded_polyline = direction_info[0]['overview_polyline']['points']
        params = {
            'size': '800x800',
            'maptype': 'roadmap',
            'key': self.gmaps.key,
            'path': f'color:0xff0000ff|weight:5|enc:{encoded_polyline}',
            'markers': '|'.join([f"{wp['lat']},{wp['lng']}" for wp in waypoints_ordered])
        }

        response = requests.get(base_url, params=params)
        order_name = order.split("\\")[1]

        with open(f"{self.image_save_path}/{order_name}_route_map.png", 'wb') as file:
            file.write(response.content)
