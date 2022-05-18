import pandas as pd
import numpy as np
import altair as alt
import gpxpy
import haversine as hs
import streamlit as st
import folium
from streamlit_folium import folium_static

st.title('GPX file dashboard')

# file = st.file_uploader("Upload a GPX file", type=["gpx"], accept_multiple_files=False)

# if file is not None:
#     gpx = gpxpy.parse(file)
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

skip = 10
route_df = route_df[::skip]

route_df['elevation_diff'] = route_df['elevation'].diff()
route_df['time_diff'] = [] + list(route_df['time'].diff().apply(lambda x: x/np.timedelta64(1, 's')))
route_df['speed'] = route_df['distance']/route_df['time_diff'] * 18 / 5 * 10
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

df = route_df[['latitude', 'longitude', 'elevation', 'time', 'distance',
       'elevation_diff', 'time_diff', 'speed', 'total_dist', 'km',
       'net_elevation']]
df['total_dist'] = df['total_dist']/100
df['speed-km/h'] = df['speed'].rolling(30).mean()

# st.dataframe(df)
# add average speed, total elevation, total time, date time etc
st.map(df)


# call to render Folium map in Streamlit
st_data = st_folium(m, width = 725)

# ALTAIR VIZ

line = alt.Chart(df.iloc[::50, :]).mark_line().encode(
    x = alt.X('total_dist'),
    y = alt.Y('elevation')
)
nearest = alt.selection(type='single', nearest=True, on='mouseover',
                        fields=['total_dist'], empty='none')

selectors = alt.Chart(df.iloc[::50, :]).mark_point().encode(
    x='total_dist',
    opacity=alt.value(0),
).add_selection(
    nearest
)
points = line.mark_point(color='red').encode(
    opacity=alt.condition(nearest, alt.value(1), alt.value(0))
)
rules = alt.Chart(df.iloc[::50, :]).mark_rule(color='gray').encode(
    x='total_dist',
).transform_filter(
    nearest
)
speed = alt.Chart(df.iloc[::50, :]).mark_line().encode(
    x = alt.X('total_dist'),
    y = alt.Y('speed-km/h'),
    order='total_dist'
)
a = line.mark_area(opacity=0.5) + selectors + points + rules
b = speed + rules

final = alt.layer(a,b).resolve_scale(
    y = 'independent'
)

st.altair_chart(final,use_container_width=True)

if __name__=="__main__":
    main()