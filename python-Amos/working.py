from turtle import color
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import haversine as hs
import folium


route_df = pd.read_csv('./python-Amos/route_df.csv')

# add elevation difference
route_df['elevation_diff'] = route_df['elevation'].diff()

# create a haversine function to calculate distance
def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    distance = hs.haversine(
            point1 = (lat1,lon1),
            point2 = (lat2,lon2),
            unit = hs.Unit.METERS
    )
    return np.round(distance, 2)

# loop it for all points
distances = [np.nan]
for i in range(len(route_df)):
    if i == 0:
        continue
    else:
        distances.append(haversine_distance(
            lat1=route_df.iloc[i - 1]['latitude'],
            lon1=route_df.iloc[i - 1]['longitude'],
            lat2=route_df.iloc[i]['latitude'],
            lon2=route_df.iloc[i]['longitude']
        ))
        
route_df['distance'] = distances

# create colums for plotting distance to elevation
route_df['cum_elevation'] = route_df['elevation_diff'].cumsum()
route_df['cum_distance'] = route_df['distance'].cumsum()

fig = plt.figure(figsize=(10,4))
plt.plot(
    route_df['cum_distance']/1000,
    route_df['cum_elevation'],
    lw=2.5,
    color='steelblue')
plt.xlabel('Distance (KM)')
plt.ylabel('Elevation (m)')
plt.savefig("elevation.png")
plt.show()


# USING FOLIUM TO PLOT INTERACTIVE MAP

# create coordinates
coordinates = [tuple(x) for x in route_df[['latitude','longitude']].to_numpy()]

m = folium.Map(
    location=[24.5, 121.4],
    zoom_start=9,
    tiles='Stamen Terrain'
)

start = folium.Marker(location=[24.674256,121.768730],popup="Starting Point",tooltip=folium.Tooltip("Start",permanent=True))
start.add_to(route_df)
end = folium.Marker(location=[23.965011,120.974105],popup="End Point",tooltip=folium.Tooltip("End",permanent=True))
end.add_to(m)

folium.PolyLine(coordinates,weight=6).add_to(m)

m.save('map.html')
display(m)