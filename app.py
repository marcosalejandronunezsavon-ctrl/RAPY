from flask import Flask
import requests
from bs4 import BeautifulSoup
import threading
import time
import json
import os
import re

app = Flask(__name__)

ARCHIVO_TASAS = "tasas.json"

tasas = {
    "USD": 0.0,
    "EUR": 0.0,
    "MLC": 0.0,
    "CUP": 1.0
}

anteriores = {
    "USD": 0.0,
    "EUR": 0.0,
    "MLC": 0.0
}

def guardar_tasas():
    try:
        with open(ARCHIVO_TASAS, "w", encoding="utf-8") as f:
            json.dump(tasas, f)
    except:
        pass

def cargar_tasas():
    global tasas
    try:
        if os.path.exists(ARCHIVO_TASAS):
            with open(ARCHIVO_TASAS, "r", encoding="utf-8") as f:
                datos = json.load(f)
                tasas.update(datos)
    except:
        pass

def obtener_html():
    url = "https://eltoque.com/tasas-de-cambio-cuba/mercado-informal"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    return r.text

def extraer_tasa(texto, moneda, valor_actual):
    try:
        patron = rf"1\s*{moneda}\s*=\s*([\d.,]+)"
        m = re.search(patron, texto)
        if m:
            return float(m.group(1).replace(",", "."))
    except:
        pass
    return valor_actual

def actualizar_tasas():
    global tasas, anteriores
    while True:
        try:
            html = obtener_html()
            soup = BeautifulSoup(html, "html.parser")
            texto = soup.get_text(" ", strip=True)

            anteriores["USD"] = tasas["USD"]
            anteriores["EUR"] = tasas["EUR"]
            anteriores["MLC"] = tasas["MLC"]

            nuevo_usd = extraer_tasa(texto, "USD", tasas["USD"])
            nuevo_eur = extraer_tasa(texto, "EUR", tasas["EUR"])
            nuevo_mlc = extraer_tasa(texto, "MLC", tasas["MLC"])

            if nuevo_usd > 0:
                tasas["USD"] = nuevo_usd
            if nuevo_eur > 0:
                tasas["EUR"] = nuevo_eur
            if nuevo_mlc > 0:
                tasas["MLC"] = nuevo_mlc

            guardar_tasas()
            print("Tasas actualizadas:", tasas)

        except Exception as e:
            print("Sin internet o error obteniendo tasas:", e)
            print("Se mantienen las últimas tasas guardadas:", tasas)

        time.sleep(300)

def estado_moneda(moneda):
    actual = tasas[moneda]
    anterior = anteriores[moneda]

    if actual > anterior:
        return "▲", "sube"
    elif actual < anterior:
        return "▼", "baja"
    else:
        return "●", "igual"

@app.route("/")
def inicio():
    flecha_usd, clase_usd = estado_moneda("USD")
    flecha_eur, clase_eur = estado_moneda("EUR")
    flecha_mlc, clase_mlc = estado_moneda("MLC")

    html = f"""
    <html>
    <head>
        <title>RAPY</title>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="300">
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                background: #f2f2f2;
                margin: 0;
                padding: 0;
            }}
            .menu {{
                position: absolute;
                top: 15px;
                left: 20px;
                font-size: 28px;
                cursor: pointer;
            }}
            .caja {{
                background: white;
                padding: 20px;
                margin: 20px auto;
                width: 320px;
                border-radius: 10px;
                box-shadow: 0px 0px 10px gray;
            }}
            button {{
                padding: 10px;
                margin: 5px;
                background: #2ecc71;
                border: none;
                color: white;
                border-radius: 5px;
                cursor: pointer;
            }}
            input, select {{
                padding: 8px;
                margin: 5px;
                width: 150px;
            }}
            .sube {{
                color: green;
                font-weight: bold;
            }}
            .baja {{
                color: red;
                font-weight: bold;
            }}
            .igual {{
                color: gray;
                font-weight: bold;
            }}
            .fila {{
                margin: 8px 0;
                display: block;
            }}
        </style>
        <script>
            function convertir() {{
                let cantidad = parseFloat(document.getElementById("cantidad").value) || 0;
                let origen = document.getElementById("origen").value;
                let destino = document.getElementById("destino").value;

                let tasas = {{
                    "USD": {tasas["USD"]},
                    "EUR": {tasas["EUR"]},
                    "MLC": {tasas["MLC"]},
                    "CUP": 1
                }};

                let cup = cantidad * tasas[origen];
                let resultado = cup / tasas[destino];

                document.getElementById("resultado").innerHTML =
                    cantidad + " " + origen + " = " + resultado.toFixed(2) + " " + destino;
            }}

            function publicar() {{
                let texto = document.getElementById("oferta").value;
                if (texto.trim() === "") return;
                let lista = document.getElementById("mercado");
                let item = document.createElement("li");
                item.innerText = texto;
                lista.appendChild(item);
                document.getElementById("oferta").value = "";
            }}
        </script>
    </head>
    <body>
        <div class="menu">☰</div>
        <h1>💲RAPY💲</h1>

        <div class="caja">
            <b>Tasas actuales</b><br><br>
            <div class="fila">1 USD 🇺🇸 = {tasas["USD"]:.2f} CUP <span class="{clase_usd}">{flecha_usd}</span></div>
            <div class="fila">1 EUR 🇪🇺 = {tasas["EUR"]:.2f} CUP <span class="{clase_eur}">{flecha_eur}</span></div>
            <div class="fila">1 MLC 💳 = {tasas["MLC"]:.2f} CUP <span class="{clase_mlc}">{flecha_mlc}</span></div>
        </div>

        <div class="caja">
            <h3>Convertidor de moneda</h3>
            <input id="cantidad" placeholder="Cantidad"><br>
            <select id="origen">
                <option>USD</option>
                <option>CUP</option>
                <option>EUR</option>
                <option>MLC</option>
            </select>
            <select id="destino">
                <option>CUP</option>
                <option>USD</option>
                <option>EUR</option>
                <option>MLC</option>
            </select><br>
            <button onclick="convertir()">Convertir</button>
            <p id="resultado"></p>
        </div>

        <div class="caja">
            <h3>Publicar oferta</h3>
            <input id="oferta" placeholder="Ej: Vendo 100 USD en La Habana"><br>
            <button onclick="publicar()">Publicar</button>
            <ul id="mercado"></ul>
        </div>
    </body>
    </html>
    """
    return html

cargar_tasas()

hilo = threading.Thread(target=actualizar_tasas)
hilo.daemon = True
hilo.start()
