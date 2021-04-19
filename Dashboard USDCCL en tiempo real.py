import pandas as pd
import websocket
import time
import threading
import json
import re
import requests
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Output, Input

tabla = pd.read_excel("Listado Cedears.xlsx", index_col="ticker")
tickers = tabla.index.to_list()

with open("c.json") as json_file:
    archivo = json.load(json_file)
username = archivo["pyrofex"]["usuario"]
password = archivo["pyrofex"]["contraseña"]
token = archivo["finnhub"]["token"]

def ws_cedears():
    def StringBetween(text, left, right):
        return re.search(left + '(.*?)' + right, text).group(1)

    url = "https://api.primary.com.ar/rest/users/login"
    headers = {"Host": "api.primary.com.ar",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "deflate",
        "Referer": "https://web.talaris.com.ar/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Cache-control": "no-cache",
        "Origin": "https://web.talaris.com.ar",
        "Pragma": "no-cache"}
    
    data = json.dumps({"username": username, "password": password, "brokerId": 407})  # 407 es ECO, cambiar si se trata de otro

    response = requests.post(url=url, headers=headers, data=data)
    status = response.status_code
    if status != 200:
        print("Error, Etapa I")
        quit()
    respuesta = json.loads(response.text)
    if respuesta["message"] != "User is Authenticated.":
        print("usuario y/o contrasenia erroneos")
        quit()
    text = response.headers['Set-Cookie']
    cookie = StringBetween(text, "", ";")

    productos = []
    for ticker in tabla["ticker cedear"]:
        productos.append({"symbol": "MERV - XMEV - " + ticker + " - 48hs", "marketId": "ROFX"})

    send = json.dumps({"type": "smd", "level": 1,  # Acá se vé que se pide en el websocket
                       "entries": ["BI", "OF"],#, "LA", "OP", "CL", "SE", "OI", "LO", "HI", "IV", "TV", "EV", "NV"],
                       "depth": 1, "products": productos})

    def on_message(ws, message):
        dict_message = json.loads(message)
        try:
            ticker_msg = dict_message["instrumentId"]["symbol"][14:-7]
            offer = dict_message["marketData"]["OF"][0]["price"]
            bid = dict_message["marketData"]["BI"][0]["price"]
            tabla.loc[tabla.index == ticker_msg, ["compra","venta"]] = offer, bid
            print("Nuevo valor de ------- CEDEAR de " + ticker_msg, offer, bid, "        Hora: ", time.strftime('%H:%M:%S', time.gmtime(((dict_message["timestamp"]) - 10800000) / 1000.)))
        except:
            print("Error en la lectura del mensaje de PYROFEX: \n", dict_message)
    def on_error(ws, error):
        print("Error en ws de cedears: " + error)
    def on_open(ws):
        print("CONNECTED TO PYROFEX")
        ws.send(send)
        print("CEDEARS SUSCRIPTOS")
    def on_close(ws):
        print("DISCONNECTED FROM PYROFEX")

    host = "wss://api.primary.com.ar/"

    ws = websocket.WebSocketApp(host, on_message=on_message, on_error=on_error, on_close=on_close, on_open=on_open, cookie=cookie)
    ws.run_forever()

def ws_acciones():
    def on_message(ws, message):
        dict_message = json.loads(message)
        try:
            for nombre_recibido in dict_message["data"]:
                ticker_msg = nombre_recibido["s"]
                precio_recibido = nombre_recibido["p"]
                tabla.loc[tabla.index == ticker_msg, ["accion"]] = precio_recibido

                print("Nuevo valor de ------- ACCION de "+ ticker_msg, precio_recibido, "        Hora: ", time.strftime('%H:%M:%S', time.gmtime(((nombre_recibido["t"]) - 10800000) / 1000.)))
        except:
            print("Error en la lectura del mensaje de FINNHUB\n", dict_message)
    def on_error(ws, error):
        print("Error en ws de acciones: ", error)
    def on_close(ws):
        print("DISCONNECTED FROM FINNHUB")
    def on_open(ws):
        global tickers
        print("CONNECTED TO FINNHUB")
        for ticker in tabla["ticker cedear"].to_list():
            ws.send('{"type":"subscribe","symbol":"'+ticker+'"}')
        print("ACCIONES SUSCRIPTAS")

    url = "wss://ws.finnhub.io?token=" + token
    ws = websocket.WebSocketApp(url, on_message = on_message, on_error = on_error, on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

def pagina_web():
    app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
    app.title = "CCL de CEDEARS"

    app.layout = html.Div([
        html.Div(dcc.Graph(id="id_grafico")),
        html.Div(dcc.Interval(id='update', interval=2000, n_intervals=1)),
    ])

    @app.callback(Output('id_grafico', 'figure'), [Input('update', 'n_intervals')])
    def update_chart(time):
        tabla["ccl_compra"] = tabla["compra"]/tabla["accion"]*tabla["ratio"]
        tabla["ccl_venta"] = tabla["venta"]/tabla["accion"]*tabla["ratio"]
        prom_compra = tabla["ccl_compra"].mean()
        prom_venta = tabla["ccl_venta"].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tickers, y=tabla["ccl_compra"], showlegend=True, name="compra", mode="markers", text="aaa"))
        fig.add_trace(go.Scatter(x=tickers, y=tabla["ccl_venta"], showlegend=True, name="venta", mode="markers", text=tabla["spread"]))
        fig.add_hline(y=prom_compra, line_dash="dash", line_color="blue", annotation_text="Compra: $"+ str(round(prom_compra,1)), annotation_position="top right")
        fig.add_hline(y=prom_venta, line_dash="dash", line_color="red", annotation_text="Venta: $"+ str(round(prom_venta,1)), annotation_position="bottom right")
        fig.update_xaxes(type='category', tickangle=-90)#, categoryorder='category ascending')
        fig.update_layout(
            title={'text': "CCL de CEDEARS",
                'y': 0.99,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'},
            yaxis_title="USD CCL [$]",
            legend_title="",#"Datos: ",
            font=dict(family="Arial",
                size=14,
                color="RebeccaPurple"),
            showlegend=True,
            legend=dict(orientation="h",
                yanchor="bottom",
                y=1,
                xanchor="right",
                x=1),
            margin=dict(l=20, r=20, t=80, b=0)
        )
        
        fig.add_annotation(dict(font=dict(color='black', size=14),
                                x=0.01,
                                y=1.01,
                                showarrow=True,
                                text="Variación Compra: $"+ str(round(tabla["ccl_compra"].std(),2)) +
                                     "        Variación Venta: $"+ str(round(tabla["ccl_venta"].std(),2)) +
                                     "        Diferencia Promedios: $" + str(round(prom_compra-prom_venta, 2)) +
                                     "        Spread(%): " + str(round((1-prom_venta/prom_compra)*100, 2)) +" %",
                                xanchor='left',
                                xref="paper",
                                yref="paper")
                           )
        fig.update_annotations(
            font=dict(family="Arial",
                      size=14,
                      color="RebeccaPurple")
        )
    app.run_server(debug=True, port=2999)

#Separación de los procesos
Datos=threading.Thread(target=ws_acciones)
Datos.daemon = True
Datos.start()

Datos=threading.Thread(target=ws_cedears)
Datos.daemon = True
Datos.start()

Datos=threading.Thread(target=pagina_web())
Datos.daemon = True
Datos.start()