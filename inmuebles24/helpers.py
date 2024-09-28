import re
import logging as log
from bs4 import BeautifulSoup as bs
from urllib import parse

log.basicConfig(level = log.INFO)

regex = r"[-+]?(?:\d*\.\d+|\d+)"

DENOMINATION_MXN = "MXN"
DENOMINATION_USD = "USD"

class Inmuebles24(object):
  propiedad = ''
  tipo = ''
  precio = 0
  denominacion = DENOMINATION_MXN
  visualizaciones = 0
  metros_total = 0
  metros_construido = 0
  banos = 0
  medio_banos = 0
  estacionamientos = 0
  recamaras = 0
  antiguedad = 0
  tiempo_de_publicacion = ''
  status_desarrollo = ''
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
    self.visualizaciones = 0
    self.metros_total = 0
    self.metros_construido = 0
    self.banos = 0
    self.medio_banos = 0
    self.estacionamientos = 0
    self.recamaras = 0
    self.antiguedad = 0
    self.tiempo_de_publicacion = ''
    self.status_desarrollo = ''
    self.ubicacion = ''
    self.url = ''
    self.descripcion = ''
    self.latitud = 0
    self.longitud = 0

def obtener_numero_de_texto(string: str, return_zero: bool = False):
  if string:
    number_list = re.findall(regex, string)
    number = ''.join(number_list)

    if is_int(number):
      return int(number)
    elif es_float(number):
      return float(number)
  
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
  contenedor_principal = soup.find('div', id='article-container')
  contenedor_titulo = contenedor_principal.find('hgroup', class_='title-container')
  contenedor_vistas = contenedor_principal.find('div', id='user-views')

  mapa = None
  try:
    mapa = contenedor_principal.find('img', id='static-map')
  except:
    log.warn("No se pudo obtener el mapa")

  # Datos

  datos = Inmuebles24()

  # Precio

  try:
    precio_html = contenedor_principal.find('div', class_='price-item-container').find('div', class_='price-value').find('span').find('span')

    if precio_html:
      datos.precio = obtener_numero_de_texto(precio_html.text)
      datos.denominacion = DENOMINATION_USD if "USD" in precio_html.text else DENOMINATION_MXN
  except:
    log.warn("No hay precio disponible")

  # Título

  try:
    titulo_html = contenedor_principal.find('h1', class_='title-property')
    print(titulo_html)

    if titulo_html:
      print(titulo_html.text)
      datos.propiedad = titulo_html.text.strip()
  except:
    log.warn("Propiedad sin título")

  # Visualizaciones

  try:
    visualizaciones_html = contenedor_vistas.find('div').find_all('div')[-1]

    if visualizaciones_html:
      datos.visualizaciones = obtener_numero_de_texto(visualizaciones_html.text)
  except:
    log.warn("Propiedad sin visualizaciones")




# Características
  caracteristicas_html = None

  try:
    #caracteristicas_html = contenedor_titulo.find('ul', class_='section-icon-features').find_all('li', class_='icon-feature')
    caracteristicas_html = contenedor_titulo.find('ul', id='section-icon-features-property').find_all('li', class_='icon-feature')
  except:
    log.warn("Propiedad sin caracteristicas")

  if caracteristicas_html:
    # M2 total
    datos.metros_total = obtener_numero_de_texto(caracteristicas_html[0].text)
    
    # Si no es un terreno "Terreno"
    if len(caracteristicas_html) > 1:
      datos.metros_construido = obtener_numero_de_texto(caracteristicas_html[1].text)
      datos.antiguedad = obtener_numero_de_texto(caracteristicas_html[-1].text, True)
      for element in caracteristicas_html[2:]:
        text = element.text
        if 'medio baño' in text or 'medios baños' in text:
          datos.medio_banos = obtener_numero_de_texto(text, True)
        elif 'baño' in text or 'baños' in text:
          datos.banos = obtener_numero_de_texto(text, True)
        elif 'estac' in text:
          datos.estacionamientos = obtener_numero_de_texto(text, True)
        elif 'rec' in text:
          datos.recamaras = obtener_numero_de_texto(text, True)

  # Tiempo de publicación

  try:
    publicacion_html = contenedor_vistas.find('div').find_all('div')[0]

    if publicacion_html:
      datos.tiempo_de_publicacion = publicacion_html.text.strip()
  except:
    log.warn("Propiedad sin fecha de publicación")

  # Tipo de propiedad

  try:
    tipo_html = contenedor_principal.find('h2', class_='title-type-sup-property')

    if tipo_html:
      datos.tipo = tipo_html.text.split('·')[0].strip()
  except:
    log.warn("Propiedad sin tipo definido")

  # Estatus de desarrollo

  try:
    estatus_html = contenedor_principal.find('div', class_='price-item-container').find('div', class_='price-value').find('span')

    if estatus_html:
      datos.status_desarrollo = estatus_html.text.split(' ')[0].strip()
  except:
    log.warn("Propiedad sin estatus")

  # Ubicación

  try:
    #ubicacion_html = contenedor_principal.find('h2', class_='title-location')
    ubicacion_html = contenedor_principal.find('h4')

    if ubicacion_html:
      datos.ubicacion = ubicacion_html.text.strip().replace("Ver en mapa", "").replace("\n", "").replace("\r", "")
  except:
    log.warn("Propiedad sin ubicación")

# Obtener latitud y longitud desde el mapa
  if mapa:
    try:
      map_url = mapa.get('src')
      location = parse.parse_qs(parse.urlparse(f'https:{map_url}').query).get('center')[0].split(',')

      datos.latitud = location[0]
      datos.longitud = location[1]
    except:
      log.warn("Error intentando obtener locacion")


  # Descricion

  try:
    html = contenedor_principal.find('div', id='longDescription')

    if html:
      datos.descripcion = html.text.strip().replace("\n", "").replace("\r", "")
  except:
    log.warn("Propiedad ubicación")


  return datos