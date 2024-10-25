import json, os
import numpy as np
from dotenv import load_dotenv
import pandas as pd
import geopandas as gpd
from shapely import wkt
import plotly.graph_objects as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

#### 외부 변수 로드 (mapbox 토큰)
load_dotenv()
mapbox_accesstoken = os.getenv('mapbox_accesstoken')

#### 데이터 로드 & 전처리
# 서울시 경계 GeoJSON 파일 로드
with open('../data/서울_자치구_경계_2017.geojson') as f:
    seoul_geojson = json.load(f)

# 서울시 경계 SHP 파일 로드
region = gpd.read_file('../data/sig_20230729/sig.shp', encoding='cp949')
seoul_gu = region[region['SIG_CD'].str[0:2] == '11'].copy()
seoul_gu.crs = "epsg:5179"
seoul_gu = seoul_gu.to_crs('EPSG:4326')

# 교통사고 데이터 전처리
acdnt_df = pd.read_csv('../data/acdnt_df2.csv')
acdnt_gdf = gpd.GeoDataFrame(acdnt_df[['acdnt_no', 'acdnt_dd_dc', 'acdnt_gae_dc', 'latitude', 'longitude']],
                             geometry=gpd.points_from_xy(acdnt_df['longitude'], acdnt_df['latitude']),
                             crs='EPSG:4326')

# 상가 데이터 전처리
store_df = pd.read_csv('../data/상가필터링.csv')
store_gdf = gpd.GeoDataFrame(store_df,
                             geometry=gpd.points_from_xy(store_df['경도'], store_df['위도']),
                             crs='EPSG:4326')

# 노인복지시설 데이터 전처리
snwf_df = pd.read_csv('../data/welfare2_df5.csv')
snwf_gdf = gpd.GeoDataFrame(snwf_df[['시설코드', '시설명', '시설_중분류', 'latitude', 'longitude']],
                             geometry=gpd.points_from_xy(snwf_df['longitude'], snwf_df['latitude']),
                             crs='EPSG:4326')

# 지하철출입구 데이터 전처리
subway_df = pd.read_csv('../data/subway_df.csv')
subway_df['geometry'] = subway_df['geometry'].apply(wkt.loads)
subway_gdf = gpd.GeoDataFrame(subway_df[['ENTRC_NO', 'geometry']], geometry='geometry')
subway_gdf.set_crs(epsg=4326, inplace=True)

# 버스정류장 데이터 전처리
busstop_df = pd.read_csv('../data/busstop_df.csv')
busstop_gdf = gpd.GeoDataFrame(busstop_df[['정류소명', '정류소타입', 'X좌표', 'Y좌표']],
                             geometry=gpd.points_from_xy(busstop_df['X좌표'], busstop_df['Y좌표']),
                             crs='EPSG:4326')

# 교차로 데이터 전처리
crossroad_df = pd.read_csv('../data/crossroad_df.csv')
crossroad_gdf = gpd.GeoDataFrame(crossroad_df[['교차로관리번호', '교차로명칭', 'X좌표', 'Y좌표']],
                                 geometry=gpd.points_from_xy(crossroad_df['X좌표'], crossroad_df['Y좌표']),
                                 crs='EPSG:5186')
crossroad_gdf = crossroad_gdf.to_crs('EPSG:4326')

# 횡단보도 데이터 전처리
crosswalk_df = pd.read_csv('../data/crosswalk_df.csv')
crosswalk_gdf = gpd.GeoDataFrame(crosswalk_df[['횡단보도관리번호', 'X좌표', 'Y좌표']],
                                 geometry=gpd.points_from_xy(crosswalk_df['X좌표'], crosswalk_df['Y좌표']),
                                 crs='EPSG:5186')
crosswalk_gdf = crosswalk_gdf.to_crs('EPSG:4326')

# 도시공원 데이터 전처리
park_df = pd.read_csv('../data/park_df.csv')
park_df['geometry'] = park_df['geometry'].apply(wkt.loads)
park_gdf = gpd.GeoDataFrame(park_df[['LABEL', 'geometry']], geometry='geometry')
park_gdf = park_gdf.set_crs(epsg=4326)
geojson_park = park_gdf.__geo_interface__

# 전통시장 데이터 전처리
market_df = pd.read_csv('../data/local_market_df.csv')
market_df['geometry'] = market_df['geometry'].apply(wkt.loads)
market_gdf = gpd.GeoDataFrame(market_df[['TRDAR_CD_N', 'geometry']], geometry='geometry')
market_gdf = market_gdf.set_crs(epsg=4326)
geojson_market = market_gdf.__geo_interface__

# 보호구역 데이터 전처리
prtz_df = pd.read_csv('../data/prtz_df3.csv')
prtz_df['geometry'] = prtz_df['geometry'].apply(wkt.loads)
prtz_gdf = gpd.GeoDataFrame(prtz_df[['CONTS_NAME_EXT', 'geometry']], geometry='geometry')
prtz_gdf = prtz_gdf.set_crs(epsg=4326)
geojson_prtz = prtz_gdf.__geo_interface__

# 위험도 데이터 전처리
dangerous_gdf = gpd.read_file('../data/사고위험도/points_사고위험도.shp')
dangerous_gdf = dangerous_gdf.set_crs(epsg=5179)
dangerous_gdf = dangerous_gdf.to_crs("EPSG:4326")
dangerous3_gdf = dangerous_gdf[dangerous_gdf['사고위험등']==3]
dangerous4_gdf = dangerous_gdf[dangerous_gdf['사고위험등']==4]

# 필요 없어진 변수(데이터) 삭제
del region, acdnt_df, snwf_df, subway_df, busstop_df, crossroad_df, crosswalk_df, park_df, market_df, prtz_df, dangerous_gdf


#### Dash 앱 생성
app = Dash(__name__)

#### Dash 레이아웃 정의
app.layout = html.Div([
    html.H3('2024년 데이터 분석 전문인재 양성과정 2기 - 1조클럽',
            style={
            'textAlign': 'center',
            'color': 'Black'
        }),

    # 자치구 선택 Dropdown
    dcc.Dropdown(
        id='gu-dropdown',
        options=[{'label': '전체', 'value': '전체'}] + [{'label': gu, 'value': gu} for gu in seoul_gu['SIG_KOR_NM'].unique()],
        value='전체',       # 기본 선택
        clearable=False    # 취소 버튼
    ),

    # fig 표시 구역
    dcc.Graph(
        id='figure',
        style={'width': '100%', 'height': '85vh'}  # 화면 전체에 맞게 설정 (100%, 100vh)
    )
])


#### 콜백 함수: 필터링에 따라 지도를 업데이트
@app.callback(
    Output('figure', 'figure'),
    [Input('gu-dropdown', 'value')]
)


#### 데이터 시각화 설계
def update_map(value):

    #### 필터를 데이터에 적용
    if value == '전체':
        joined_park_gdf = park_gdf
        joined_market_gdf = market_gdf
        joined_prtz_gdf = prtz_gdf
        joined_dangerous4_gdf = dangerous4_gdf
        joined_dangerous3_gdf = dangerous3_gdf
        joined_acdnt_gdf = acdnt_gdf
        joined_store_gdf = store_gdf
        joined_snwf_gdf = snwf_gdf
        joined_subway_gdf = subway_gdf
        joined_busstop_df = busstop_gdf
        joined_crossroad_gdf = crossroad_gdf
        joined_crosswalk_gdf = crosswalk_gdf
    else:
        filter_gu = seoul_gu[seoul_gu['SIG_KOR_NM']==value]
        joined_park_gdf = gpd.sjoin(park_gdf, filter_gu, how='inner', predicate='within')
        joined_market_gdf = gpd.sjoin(market_gdf, filter_gu, how='inner', predicate='within')
        joined_prtz_gdf = gpd.sjoin(prtz_gdf, filter_gu, how='inner', predicate='within')
        joined_dangerous4_gdf = gpd.sjoin(dangerous4_gdf, filter_gu, how='inner', predicate='within')
        joined_dangerous3_gdf = gpd.sjoin(dangerous3_gdf, filter_gu, how='inner', predicate='within')
        joined_acdnt_gdf = gpd.sjoin(acdnt_gdf, filter_gu, how='inner', predicate='within')
        joined_store_gdf = gpd.sjoin(store_gdf, filter_gu, how='inner', predicate='within')
        joined_snwf_gdf = gpd.sjoin(snwf_gdf, filter_gu, how='inner', predicate='within')
        joined_subway_gdf = gpd.sjoin(subway_gdf, filter_gu, how='inner', predicate='within')
        joined_busstop_df = gpd.sjoin(busstop_gdf, filter_gu, how='inner', predicate='within')
        joined_crossroad_gdf = gpd.sjoin(crossroad_gdf, filter_gu, how='inner', predicate='within')
        joined_crosswalk_gdf = gpd.sjoin(crosswalk_gdf, filter_gu, how='inner', predicate='within')


    #### 위치 정보(Point)
    # 사고위험도 위치 정보
    trace_dangerous4 = go.Scattermapbox(
        lat=joined_dangerous4_gdf.geometry.y,
        lon=joined_dangerous4_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=20,
            color='red',
        ),
        hovertext=[f'위험도: 매우높음<br>점수: {np.round(score, 2)}' for score in joined_dangerous4_gdf['사고발생_']],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='사고위험도_매우높음',
        # visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    trace_dangerous3 = go.Scattermapbox(
        lat=joined_dangerous3_gdf.geometry.y,
        lon=joined_dangerous3_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=10,
            color='orange'
        ),
        hovertext=[f'위험도: 높음<br>점수: {np.round(score, 2)}' for score in joined_dangerous3_gdf['사고발생_']],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='사고위험도_높음',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 교통사고 위치 정보
    trace_acdnt = go.Scattermapbox(
        lat=joined_acdnt_gdf.geometry.y,
        lon=joined_acdnt_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='red'
        ),
        hovertext=[f'사고번호: {acdnt_no}<br>발생일자: {acdnt_dd_dc}<br>사고유형: {acdnt_gae_dc}' for acdnt_no, acdnt_dd_dc, acdnt_gae_dc in zip(joined_acdnt_gdf['acdnt_no'], joined_acdnt_gdf['acdnt_dd_dc'], joined_acdnt_gdf['acdnt_gae_dc'])],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='교통사고',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 상가 위치 정보
    trace_store = go.Scattermapbox(
        lat=joined_store_gdf.geometry.y,
        lon=joined_store_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='blue'
            # colorscale='Viridis',
            # showscale=True
        ),
        hovertext=[f'상호명: {name}<br>상권업종(대): {top}<br>상권업종(중): {mid}' for name, top, mid in zip(joined_store_gdf['상호명'], joined_store_gdf['상권업종대분류명'], joined_store_gdf['상권업종중분류명'])],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='상가정보',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 사회복지시설(노인) 위치 정보
    trace_welfare = go.Scattermapbox(
        lat=joined_snwf_gdf['latitude'],
        lon=joined_snwf_gdf['longitude'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='blue'
        ),
        hovertext=[f'시설번호: {code}<br>시설명: {name}<br>시설유형: {type}' for code, name, type in zip(joined_snwf_gdf['시설코드'], joined_snwf_gdf['시설명'], joined_snwf_gdf['시설_중분류'])],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='노인복지시설',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 지하철출입구 위치 정보
    trace_subway = go.Scattermapbox(
        lat=joined_subway_gdf.geometry.y,
        lon=joined_subway_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='black'
        ),
        hovertext=[f'출구번호: {no}' for no in joined_subway_gdf['ENTRC_NO']],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='지하철출입구',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 버스정류장 위치 정보
    trace_busstop = go.Scattermapbox(
        lat=joined_busstop_df.geometry.y,
        lon=joined_busstop_df.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='black'
        ),
        hovertext=[f'정류소명: {name}<br>정류소유형: {type}' for name, type in zip(joined_busstop_df['정류소명'], joined_busstop_df['정류소타입'])],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='버스정류장',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 교차로 위치 정보
    trace_crossroad = go.Scattermapbox(
        lat=joined_crossroad_gdf.geometry.y,
        lon=joined_crossroad_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='green'
        ),
        hovertext=[f'관리번호: {no}<br>교차로명: {name}' for no, name in zip(joined_crossroad_gdf['교차로관리번호'], joined_crossroad_gdf['교차로명칭'])],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='교차로',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    # 횡단보도 위치 정보
    trace_crosswalk = go.Scattermapbox(
        lat=joined_crosswalk_gdf.geometry.y,
        lon=joined_crosswalk_gdf.geometry.x,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=5,
            color='green'
        ),
        hovertext=[f'관리번호: {no}' for no in joined_crosswalk_gdf['횡단보도관리번호']],  # 각 마커에 표시할 텍스트
        hoverinfo='text',
        name='횡단보도',
        visible='legendonly'    # 데이터는 기본값으로 숨김 상태
    )

    #### 공간 정보(Polygon)
    # 도시공원 공간 정보
    trace_park = go.Choroplethmapbox(
        geojson=geojson_park,  # GeoJSON 데이터
        locations=joined_park_gdf["LABEL"],  # locations 값을 'ID' 필드와 매핑
        z=[1] * len(joined_park_gdf),  # 모든 z 값을 동일하게 설정하여 색상이 동일하게 나오도록
        colorscale=[[0, 'green'], [1, 'green']],  # 모든 값에 동일한 색을 사용
        marker_opacity=0.4,  # 투명도
        marker_line_width=1,  # 경계선 너비
        featureidkey="properties.LABEL",  # GeoJSON의 속성과 매핑
        showscale=False,  # 색상 바 숨기기 (선택 사항)
        name='도시공원',
        hoverinfo='none'  # hovertext 숨기기,
    )

    # 전통시장 공간 정보
    trace_market = go.Choroplethmapbox(
        geojson=geojson_market,  # GeoJSON 데이터
        locations=joined_market_gdf["TRDAR_CD_N"],  # locations 값을 'ID' 필드와 매핑
        z=[1] * len(joined_market_gdf),  # 모든 z 값을 동일하게 설정하여 색상이 동일하게 나오도록
        colorscale=[[0, 'yellow'], [1, 'yellow']],  # 모든 값에 동일한 색을 사용
        marker_opacity=0.5,  # 투명도
        marker_line_width=1,  # 경계선 너비
        featureidkey="properties.TRDAR_CD_N",  # GeoJSON의 속성과 매핑
        showscale=False,  # 색상 바 숨기기 (선택 사항)
        name='전통시장',
        hoverinfo='none', # hovertext 숨기기
    )

    # 보호구역 공간 정보
    trace_prtz = go.Choroplethmapbox(
        geojson=geojson_prtz,  # GeoJSON 데이터
        locations=joined_prtz_gdf["CONTS_NAME_EXT"],  # locations 값을 'ID' 필드와 매핑
        z=[1] * len(joined_prtz_gdf),  # 모든 z 값을 동일하게 설정하여 색상이 동일하게 나오도록
        colorscale=[[0, 'blue'], [1, 'blue']],  # 모든 값에 동일한 색을 사용 (여기서는 'blue')
        marker_opacity=0.7,  # 투명도
        marker_line_width=1,  # 경계선 너비
        featureidkey="properties.CONTS_NAME_EXT",  # GeoJSON의 속성과 매핑
        showscale=False,  # 색상 바 숨기기 (선택 사항)
        name='노인보호구역',
        hovertext=[f'{name}' for name in joined_prtz_gdf['CONTS_NAME_EXT']],  # 각 마커에 표시할 텍스트
        hoverinfo='text'  # hovertext 숨기기,
    )

    # 지도 레이아웃 설정
    layout = go.Layout(
        mapbox=dict(
            accesstoken=mapbox_accesstoken,
            # style="carto-positron",  # 배경 지도 스타일
            # style="mapbox://styles/mapbox/streets-v11",
            style="mapbox://styles/mapbox/light-v11",
            zoom=11,
            center=dict(lat=joined_acdnt_gdf['latitude'].mean(), lon=joined_acdnt_gdf['longitude'].mean()), 
            # center=dict(lat=37.33066, lon=127.59196), 
        ),
        showlegend=True,
        margin={"r":0,"t":30,"l":0,"b":0},  # 여백 설정
        autosize=True,  # 자동 크기 조정
        height=None,  # 고정된 높이를 설정하지 않음
    )

    fig = go.Figure(data=[trace_park,
                          trace_market,
                          trace_prtz,
                          trace_dangerous4,
                          trace_dangerous3,         
                          trace_acdnt,
                          trace_store,
                          trace_welfare, 
                          trace_crossroad,
                          trace_crosswalk,
                          trace_subway,
                          trace_busstop,
                          ], layout=layout)
    
    if value != '전체':
        fig.update_layout(mapbox=dict(
            # style="mapbox://styles/mapbox/streets-v11",
            zoom=13
            )
        )
        fig.data[3].visible = True
        fig.data[4].visible = True
    
    # fig.update_geos(fitbounds="locations", visible=False)

    output_path = "../output/Dash.html"

    # 파일 존재 여부 확인
    if not os.path.exists(output_path):
        fig.write_html(output_path)

    return fig

#### 애플리케이션 실행
# http://127.0.0.1:8050/
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
    # app.run_server(port=8050, debug=True)