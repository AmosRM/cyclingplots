import pandas as pd
import numpy as np
import altair as alt
import gpxpy
import haversine as hs

with open('../gpx/yilan-wulling.gpx', 'r') as gpx_file:
    gpx = gpxpy.parse(gpx_file)

route_info = []

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
           route_info.append({
               'latitude': point.latitude,
               'longitude': point.longitude,
               'elevation': point.elevation,
               'time': point.time
           })

route_df = pd.DataFrame(route_info)

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    distance = hs.haversine(
            point1 = (lat1,lon1),
            point2 = (lat2,lon2),
            unit = hs.Unit.METERS
    )
    return np.round(distance, 2)
    
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


route_df['elevation_diff'] = route_df['elevation'].diff()
route_df['time_diff'] = [0] + list((route_df.loc[1:,'time'].values - route_df.loc[:(route_df.shape[0]-2),'time'].values)/np.timedelta64(1,'s'))
route_df['speed'] = route_df['distance']/route_df['time_diff']
route_df['total_dist'] = np.cumsum(route_df['distance'])
route_df['km'] = np.ceil((route_df['total_dist']+0.01)/1000)
route_df = route_df.fillna(0)
route_df['km'] = route_df['km'].astype('int')

grouped = route_df.groupby('km').agg({'time':['min','max'],'elevation':['first','last']})
grouped['net_elevation'] = grouped['elevation']['last'] - grouped['elevation']['first']
grouped['net_time'] = grouped['time']['max'] - grouped['time']['min']
# .apply(lambda x:'{0,.0f}:{1:02d}'.format(np.floor(x.total_seconds()/60)))
grouped.columns = grouped.columns.get_level_values(0)

route_df = route_df.join(grouped.loc[:, ['net_elevation','net_time']], how='left', on='km')

