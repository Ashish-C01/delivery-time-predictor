from dash import Dash, html, dcc, Output, Input, State
import dash_bootstrap_components as dbc
import folium
import folium.map
from geopy.geocoders import Nominatim
import requests
import json
import pickle
import pandas as pd
import jinja2
from jinja2 import Template
from folium import Marker

model = pickle.load(open('model2.pkl', 'rb'))

tmpldata = """<!-- Modified Marker template -->
{% macro script(this, kwargs) %}
    var {{ this.get_name() }} = L.marker(
        {{ this.location|tojson }},
        {{ this.options|tojson }}
    ).addTo({{ this._parent.get_name() }}).on('click', onClick).on('dragend', function(e) {
        var newLat = e.target.getLatLng().lat;
        var newLng = e.target.getLatLng().lng;
        var markerData = { id: e.target.options.id, lat: parseFloat(newLat), lng: parseFloat(newLng) };
        localStorage.setItem('marker-data-store', JSON.stringify(markerData));
    });
{% endmacro %}
"""

Marker._mytemplate = Template(tmpldata)


def myMarkerInit(self, *args, **kwargs):
    self.__init_orig__(*args, **kwargs)
    self._template = self._mytemplate


Marker.__init_orig__ = Marker.__init__
Marker.__init__ = myMarkerInit
m = folium.Map()


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
geolocator = Nominatim(user_agent="delivery_time")
distance = None
cords = dict()
app.title = "Delivery Time Estimator"
app.layout = html.Div(
    [
        dbc.Row(
            dbc.Col(
                html.H1(
                    "Delivery Time Prediction",
                    style={
                        "textAlign": "center",
                        "color": "#2c3e50",
                        "marginBottom": "20px",
                    },
                ),
                width=12,
            )
        ),
        dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Delivery Person Age"),
                                dcc.Input(
                                    id="delivery_person_age",
                                    placeholder="Enter Age",
                                    type="number",
                                    className="form-control",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Delivery Person Rating"),
                                dcc.Input(
                                    id="delivery_person_rating",
                                    placeholder="Enter Rating (1-5)",
                                    type="number",
                                    min=1,
                                    max=5,
                                    className="form-control",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Vehicle Type"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Motorcycle",
                                            "value": "motorcycle"},
                                        {"label": "Scooter", "value": "scooter"},
                                        {
                                            "label": "Electric Scooter",
                                            "value": "electric_scooter",
                                        },
                                    ],
                                    placeholder="Select Vehicle Type",
                                    id="vehicle",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Weather Condition"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Fog", "value": "Fog"},
                                        {"label": "Stormy", "value": "Stormy"},
                                        {"label": "Cloudy", "value": "Cloudy"},
                                        {"label": "Sandstorms",
                                            "value": "Sandstorms"},
                                        {"label": "Windy", "value": "Windy"},
                                        {"label": "Sunny", "value": "Sunny"},
                                    ],
                                    placeholder="Select Weather Condition",
                                    id="weather",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Road Traffic Density"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Low", "value": "Low"},
                                        {"label": "Medium", "value": "Medium"},
                                        {"label": "High", "value": "High"},
                                        {"label": "Jam", "value": "Jam"},
                                    ],
                                    placeholder="Select Traffic Density",
                                    id="traffic",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Number of Orders"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "0", "value": "0"},
                                        {"label": "1", "value": "1"},
                                        {"label": "2", "value": "2"},
                                        {"label": "3", "value": "3"},
                                    ],
                                    placeholder="Orders in One Attempt",
                                    id="multiple_order",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Festive Day"),
                                dcc.RadioItems(
                                    options=[
                                        {"label": "Yes", "value": "Yes"},
                                        {"label": "No", "value": "No"},
                                    ],
                                    inline=True,
                                    id="festival",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("City Type"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Metropolitan",
                                            "value": "Metropolitian"},
                                        {"label": "Urban", "value": "Urban"},
                                        {"label": "Semi-Urban",
                                            "value": "Semi-Urban"},
                                    ],
                                    placeholder="Select City Type",
                                    id="city",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Time of the Day"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Morning", "value": "Morning"},
                                        {"label": "Afternoon",
                                            "value": "Afternoon"},
                                        {"label": "Evening", "value": "Evening"},
                                        {"label": "Night", "value": "Night"},
                                    ],
                                    placeholder="Select Time",
                                    id="time",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Vehicle Condition"),
                                dcc.Dropdown(
                                    options=[
                                        {"label": "Smooth", "value": "0"},
                                        {"label": "Good", "value": "1"},
                                        {"label": "Average", "value": "2"},
                                    ],
                                    placeholder="Select Condition",
                                    id="condition",
                                ),
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label("Restaurant's Address"),
                                dcc.Input(
                                    id="res_address",
                                    placeholder="Enter Address (see info ⓘ below)",
                                    type="text",
                                    className="form-control",
                                ),
                                html.Span("ℹ️", id="info-res-address", style={
                                          "cursor": "pointer", "color": "blue", "marginLeft": "5px"}),
                                dbc.Tooltip(
                                    "If the restaurant address is not found, please provide the nearest location in the format: Street/Place Name, District. You can then drag the icon to the desired location on the map.",
                                    target="info-res-address",
                                    placement="right"
                                )
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.Label("Receiver's Address"),
                                dcc.Input(
                                    id="rec_address",
                                    placeholder="Enter Address (see info ⓘ below)",
                                    type="text",
                                    className="form-control",
                                ),
                                html.Span("ℹ️", id="info-rec-address", style={
                                          "cursor": "pointer", "color": "blue", "marginLeft": "5px"}),
                                dbc.Tooltip(
                                    "If the receiver address is not found, please provide the nearest location in the format: Street/Place Name, District. You can then drag the icon to the desired location on the map.",
                                    target="info-rec-address",
                                    placement="right"
                                )
                            ],
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button(
                                "Get Map Coordinates",
                                id="cordinate-button",
                                color="primary",
                                n_clicks=0,
                                className="d-block mx-auto mt-3",
                            ),
                            width=6,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Check Delivery Time",
                                id="submit-button",
                                color="success",
                                n_clicks=0,
                                className="d-block mx-auto mt-3",
                                disabled=True
                            ),
                            width=6,
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="loading-spinner-2",
                                type="circle",
                                children=html.Div(id="card-container"),
                            )
                        ),
                    ],
                    className="mb-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="loading-spinner1",
                                type="circle",
                                children=html.Div(
                                    id="card-container-1",
                                    className="d-flex flex-wrap justify-content-center",
                                ),

                            )
                        ),
                    ],
                    className="mb-3",
                ),
                dcc.Store(id="marker-data-store", storage_type="local"),
            ]
        ),
    ],
    style={
        "padding": "20px",
        "backgroundColor": "#f8f9fa",
        "fontFamily": "Arial, sans-serif",
    },
)


el = folium.MacroElement().add_to(m)
el._template = jinja2.Template("""
    {% macro script(this, kwargs) %}

    function onClick(e) {
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        var name_mark=e.target.options.id;
        var markerData = {id: name_mark, lat: lat, lng: lng};

        var newContent = `<p id="latlon">${name_mark}:: ${lat}, ${lng}</p>`;
        e.target.setPopupContent(newContent);
    };
    {% endmacro %}
""")


def get_prediction(data_point):
    user_input = pd.DataFrame(data_point)
    prediction = model.predict(user_input)
    return prediction[0]


@ app.callback(
    Output('card-container', 'children'),
    Input('submit-button', 'n_clicks'),
    State('delivery_person_age', 'value'),
    State('delivery_person_rating', 'value'),
    State('vehicle', 'value'),
    State('weather', 'value'),
    State('traffic', 'value'),
    State('multiple_order', 'value'),
    State('festival', 'value'),
    State('city', 'value'),
    State('time', 'value'),
    State('condition', 'value'),
)
def get_time(n_click, age, rating, vehicle, weather, traffic, order, festive, city, time, condition):
    global cords
    if n_click:
        if cords.get('restaurant_marker', 0) and cords.get('receiver_marker', 0):
            position = {"sources": [{"lat": cords['restaurant_marker'][0], "lon": cords['restaurant_marker'][1]}], "targets": [
                {"lat": cords['receiver_marker'][0], "lon": cords['receiver_marker'][1]}], "costing": "motorcycle"}
            response = requests.get(
                'https://valhalla1.openstreetmap.de/sources_to_targets', json=position)
            if response.status_code == 200:
                data = response.content
                data = json.loads(data)
                if len(data['sources_to_targets']):
                    distance = data['sources_to_targets'][0][0]['distance']
                else:
                    distance = -1
            else:
                distance = -1
        else:
            return html.Div([
                html.Br(),
                dbc.Alert(
                    "Address is missing",
                    id="alert-fade",
                    dismissable=True,
                    is_open=True,
                    color="danger"
                ),
            ])

        if distance is not None and distance != -1:
            fields = {
                "age": (age, "Delivery Person Age is a required field"),
                "rating": (rating, "Delivery Person Rating is a required field"),
                "vehicle": (vehicle, "Vehicle Type is a required field"),
                "weather": (weather, "Weather Condition is a required field"),
                "traffic": (traffic, "Road Traffic Density is a required field"),
                "order": (order, "Number of orders to be delivered in one attempt is a required field"),
                "festive": (festive, "Whether day is festive or not is a required field"),
                "city": (city, "City type is a required field"),
                "time": (time, "Time of the day is a required field"),
                "condition": (condition, "Condition of the vehicle is a required field"),
            }
            for field_name, (field_value, error_message) in fields.items():
                if not field_value:
                    return html.Div([
                        html.Br(),
                        dbc.Alert(
                            f"{error_message}",
                            id="alert-fade",
                            dismissable=True,
                            is_open=True,
                            color="danger",
                            style={'text-align': 'center'}
                        ),
                    ])
            data = {'Delivery_person_Age': [int(age)], 'Delivery_person_Ratings': [float(rating)], 'distance': [float(distance)], 'Type_of_vehicle': [vehicle], 'Weather': [weather],
                    'Road_traffic_density': [traffic], 'multiple_deliveries': [int(order)], 'Festival': [festive], 'City': [city], 'time of day': [time], 'Vehicle_condition': [int(condition)]}
            predicted_time = get_prediction(data)
            return html.Div([
                html.Br(),
                dbc.Alert(
                    f"Predicted time for delivering the food: {int(predicted_time)} minutes",
                    id="alert-fade",
                    dismissable=True,
                    is_open=True,
                    color="success",
                    style={'text-align': 'center'}
                ),
            ])
        else:
            return html.Div([
                html.Br(),
                dbc.Alert(
                    "Please set the map coordinates",
                    id="alert-fade",
                    dismissable=True,
                    is_open=True,
                    color="danger"
                ),
            ])


@ app.callback(
    Output('submit-button', 'disabled'),
    Output('card-container-1', 'children'),
    Input('cordinate-button', 'n_clicks'),
    State('res_address', 'value'),
    State('rec_address', 'value')


)
def get_map_cordinates_and_distance(click, res_add, rec_add):
    global distance
    global cords
    if not click:
        return True, html.Div([
            html.P("Click 'Get map coordinates' after entering the addresses."),
        ], style={'color': 'gray'})
    if not res_add or not rec_add:
        return True, html.Div([
            dbc.Alert(
                "Both restaurant and receiver addresses must be entered.",
                id="alert-missing-address",
                dismissable=True,
                is_open=True,
                color="danger"
            ),
        ])
    res_coordinates = geolocator.geocode(res_add)
    rec_coordinates = geolocator.geocode(rec_add)

    if not res_coordinates:
        return True, html.Div([
            html.P("Enter correct restaurant address"),
        ])
    if not rec_coordinates:
        return True, html.Div([
            html.P("Enter correct receiver address"),
        ])
    cords = {
        'restaurant_marker': [res_coordinates.latitude, res_coordinates.longitude],
        'receiver_marker': [rec_coordinates.latitude, rec_coordinates.longitude],
    }

    folium.Marker(
        [cords['restaurant_marker'][0], cords['restaurant_marker'][1]], popup=f"<p id='reslatlon'>Location of Restaurant: {cords['restaurant_marker'][0]},{cords['restaurant_marker'][1]}</p>", icon=folium.Icon(color='green', icon='utensils', prefix='fa'), id="restaurant_marker", tooltip="Click for location", draggable=True).add_to(m)
    folium.Marker(
        [cords['receiver_marker'][0], cords['receiver_marker'][1]], popup=f"<p id='reclatlon'>Location of Receiver: {cords['receiver_marker'][0]},{cords['receiver_marker'][1]}</p>", icon=folium.Icon(color='red', icon='house', prefix='fa'), tooltip="Click for location", draggable=True, id="receiver_marker").add_to(m)
    lats = [cords['restaurant_marker'][0], cords['receiver_marker'][0]]
    longs = [cords['restaurant_marker']
             [1], cords['receiver_marker'][1]]
    bounds = [[min(lats), min(longs)], [max(lats), max(longs)]]
    m.fit_bounds(bounds=bounds)

    return False, html.Iframe(srcDoc=m.get_root().render(), style={'width': '80%', 'height': '500px'})


@ app.callback(
    Input('marker-data-store', 'data'),
    Input('cordinate-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(store_data, n_clicks):
    global cords
    if n_clicks:
        if store_data:
            cords[store_data['id']] = [
                store_data.get('lat'), store_data.get('lng')]


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
