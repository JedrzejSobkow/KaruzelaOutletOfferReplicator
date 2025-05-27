from flask import Flask, render_template, redirect, url_for
import requests
import json
import time
import re

app = Flask(__name__)

CLIENT_ID = ""
CLIENT_SECRET = "" 
CODE_URL = "https://allegro.pl/auth/oauth/device"
TOKEN_URL = "https://allegro.pl/auth/oauth/token"

PRODUCT_NAMES = [
    "Stół 3M metal prostokątny 120 x 60 x 60 cm",
    "Biurko prostokątny Vasagle 140 x 60 x 120 cm czarny, dąb rustykalny",
    "3-osobowa sofa ogrodowa z poduszkami, rattan PE, czarny",
    "Furtka VidaXL 100 x Do 150 szary",
    "Klatka VidaXL 200 x 200 x 200 cm szary",
    "Regał na buty z siedziskiem Modro z wieloma półkami biało-szary",
    "Szafa Songmics MODERN 182 x 182 x 43 cm czarny",
    "Szafka na buty Vasagle 60 x 130 x 24 cm biały",
    "Skrzynia Songmics 100 x 40 x 46 cm 184l odcienie brązu",
    "HAWAJSKI DUŻY PARASOL OGRODOWY BALKONOWY SKŁADANY 200CM NA TARAS I DZIAŁKĘ",
    "Kosz na śmieci stal nierdzewna Songmics 24l czarny",
    "Wodery VidaXL 4016979 r. 45",
    "Komoda VidaXL 828056 100 x 100 x 100cm beton",
    "Fotel obrotowy Songmics biały",
    "Fotel tapicerowany tradycyjny Vasagle tkanina beżowy",
    "Krzesło ogrodowe Vida drewno brązowy",
    "EUGAD Wybieg dla królików /W",
    "KUPADUPA",
]

products_data = []


def get_code():
    try:
        payload = {'client_id': CLIENT_ID}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        api_call_response = requests.post(CODE_URL, auth=(CLIENT_ID, CLIENT_SECRET),
                                          headers=headers, data=payload)
        return api_call_response
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)


def get_access_token(device_code):
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code', 'device_code': device_code}
    return requests.post(TOKEN_URL, auth=(CLIENT_ID, CLIENT_SECRET), headers=headers, data=data)


def await_for_access_token(interval, device_code):
    while True:
        time.sleep(interval)
        result_access_token = get_access_token(device_code)
        token = json.loads(result_access_token.text)
        if result_access_token.status_code == 400:
            if token['error'] == 'slow_down':
                interval += interval
            if token['error'] == 'access_denied':
                break
        else:
            return token['access_token']


def fetch_product(access_token, phrase):
    url = "https://api.allegro.pl/sale/products"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
    params = {"phrase": phrase}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        products = response.json().get("products", [])
        for product in products:
            if product["name"] == phrase:
                return product
    return None


@app.route('/')
def index():
    code = get_code()
    result = json.loads(code.text)
    global verification_url
    verification_url = result['verification_uri_complete']
    print("User, open this address in the browser:" + verification_url)
    access_token = await_for_access_token(int(result['interval']), result['device_code'])
    print("access_token = " + access_token)

    global products_data
    products_data = []
    if access_token:
        for name in PRODUCT_NAMES:
            product = fetch_product(access_token, name)
            if product:
                products_data.append(product)
            else:
                print(f'NIE UDAŁO SIE ZAŁADOWAĆ PRODUKTU {name}')
    return redirect(url_for('show_products'))


@app.route('/products')
def show_products():
    return render_template('products.html', products=products_data, url=verification_url)


if __name__ == '__main__':
    app.run(debug=True)
