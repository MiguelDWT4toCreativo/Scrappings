import re
import logging as log
from bs4 import BeautifulSoup as bs
from urllib import parse

log.basicConfig(level=log.INFO)

DENOMINATION_MXN = "MXN"
DENOMINATION_USD = "USD"
SI = "SI"
NO = "NO"
ND = "N/D"

class Propoiedad(object):
    propiedad = ''
    tipo = ''
    precio = 0
    denominacion = DENOMINATION_MXN
    metros_total = 0
    metros_construido = 0
    banos = 0
    medio_banos = 0
    estacionamientos = 0
    recamaras = 0
    pisos = ND
    antiguedad = ''
    status_desarrollo = ''
    seguridad_privada = NO
    ubicacion = ''
    url = ''
    descripcion = ''
    latitud = 0
    longitud = 0

    def __init__(self):
        self.propiedad = ''
        self.tipo = ''
        self.precio = 0
        self.denominacion = DENOMINATION_MXN
        self.metros_total = 0
        self.metros_construido = 0
        self.banos = 0
        self.medio_banos = 0
        self.estacionamientos = 0
        self.recamaras = 0
        self.pisos = ND
        self.antiguedad = ''
        self.status_desarrollo = ''
        self.seguridad_privada = NO
        self.ubicacion = ''
        self.url = ''
        self.descripcion = ''
        self.latitud = 0
        self.longitud = 0

def obtener_numero_de_texto(string: str, return_zero: bool = False):
    if string:
        # Eliminar comas y otros caracteres que no sean dígitos o puntos decimales
        cleaned_string = re.sub(r'[^\d.]', '', string)
        
        # Si el string limpio es un número entero
        if cleaned_string.isdigit():
            return int(cleaned_string)
        # Si el string limpio es un número flotante
        elif es_float(cleaned_string):
            return float(cleaned_string)
  
    return 0 if return_zero else None

def es_float(numero_a_comprobar):
    try:
        float(numero_a_comprobar)
        return True
    except:
        return False

def is_int(value):
    try:
        int(value)
        return True
    except:
        return False

def obtener_datos(soup: bs):
    contenedor_principal = soup.find('div', class_='property-info')
    contenedor_titulo = contenedor_principal.find('div', attrs={"itemprop": "address"})

    # Datos

    datos = Propoiedad()

    # Título

    try:
        titulo_html = contenedor_titulo.find('em', attrs={"itemprop": "streetAddress"}).parent

        if titulo_html:
            datos.propiedad = titulo_html.text.strip()
    except:
        log.warn("Propiedad sin título")

    # Precio

    try:
        precio_html = contenedor_principal.find('div', class_='price-text')

        if precio_html:
            datos.precio = obtener_numero_de_texto(precio_html.text)
            datos.denominacion = DENOMINATION_MXN if "MXN" in precio_html.text else DENOMINATION_USD
    except:
        log.warn("No hay precio disponible")

    etiquetas_html = None

    try:
        etiquetas_html = contenedor_titulo.find('div', class_='section-highlighted').find_all('div')
    except:
        log.warn("Propiedad sin caracteristicas")

    if etiquetas_html:
        # Tipo de propiedad
        datos.tipo = etiquetas_html[0].text.strip()

        # Status
        datos.status_desarrollo = etiquetas_html[1].text.strip()

    # Ubicacion

    try:
        html = contenedor_titulo.find('h3', class_='location-inline')

        if html:
            datos.ubicacion = html.text.strip()
    except:
        log.warn("Propiedad sin ubicacion")

    # Lat/Lon

    try:
        html = soup.find('span', attrs={"itemprop": "geo"})

        if html:
            datos.latitud = obtener_numero_de_texto(html.find('meta', attrs={"itemprop": "latitude"})['content'])
            datos.longitud = obtener_numero_de_texto(html.find('meta', attrs={"itemprop": "longitude"})['content'])
    except:
        log.warn("Propiedad sin latitud/longitud")

    # Caracteristicas

    caracteristicas_html = None

    try:
        caracteristicas_contenedor_html = contenedor_principal.find('div', attrs={"data-gtm": "container-caracteristicas"})
        caracteristicas_html = caracteristicas_contenedor_html.find_all('div', class_='characteristic')
    except:
        log.warn("Propiedad sin caracteristicas")

    if caracteristicas_html and len(caracteristicas_html) > 0:
        for caracteristica_html in caracteristicas_html:
            texto = caracteristica_html.find('div', class_='description-text').text.casefold()
            numero = caracteristica_html.find('div', class_='description-number').text

            if 'RECÁMARAS'.casefold() == texto:
                datos.recamaras = obtener_numero_de_texto(numero)
            elif 'BAÑOS'.casefold() == texto:
                datos.banos = obtener_numero_de_texto(numero)
            elif 'ESTACIONAMIENTOS'.casefold() == texto:
                datos.estacionamientos = obtener_numero_de_texto(numero)
            elif 'No. de pisos'.casefold() == texto:
                datos.pisos = obtener_numero_de_texto(numero)
            elif 'Edad del inmueble'.casefold() == texto:
                datos.antiguedad = numero
            elif 'ÁREA TERRENO'.casefold() == texto:
                datos.metros_total = obtener_numero_de_texto(numero)
            elif 'ÁREA CONSTRUIDA'.casefold() == texto:
                datos.metros_construido = obtener_numero_de_texto(numero)

    # Amenidades

    amenidades_html = None

    try:
        amenidades_contenedor_html = contenedor_principal.find('div', attrs={"data-gtm": "container-amenidades"})
        amenidades_html = amenidades_contenedor_html.find_all('div', class_='item')
    except:
        log.warn("Propiedad sin amenidades")

    if amenidades_html and len(amenidades_html) > 0:
        for amenidad_html in amenidades_html:
            texto = amenidad_html.text.casefold()

            if 'Seguridad privada'.casefold() == texto:
                datos.seguridad_privada = SI

    # Descripción

    try:
        html = contenedor_principal.find('p', attrs={"data-testid": "property-description"})

        if html:
            datos.descripcion = html.text.strip().replace("\n", "").replace("\r", "")
    except:
        log.warn("Propiedad sin descripcion")

    return datos
