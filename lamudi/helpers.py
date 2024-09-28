import re
import logging as log
from bs4 import BeautifulSoup
from datetime import datetime

log.basicConfig(level = log.INFO)

regex = r"[-+]?(?:\d*\.\d+|\d+)"

DENOMINATION_MXN = "MXN"
DENOMINATION_USD = "USD"

# Variables objetivo
class Lamudi(object):
  precio = 0
  denominacion = DENOMINATION_MXN # USD or MX
  propiedad = ''
  metros_total = 0
  metros_construido = 0
  tiempo_de_publicacion = ''
  tipo = ''
  estacionamientos = 0
  recamaras = 0
  banos = 0
  medio_banos = 0
  seguridad_privada = 'No'
  ubicacion = ""
  url = ""
  descripcion = ""

  def __init__(self):
    self.precio = 0
    self.denominacion = DENOMINATION_MXN
    self.propiedad = ''
    self.metros_total = 0
    self.metros_construido = 0
    self.tiempo_de_publicacion = ''
    self.tipo = ''
    self.estacionamientos = 0
    self.recamaras = 0
    self.banos = 0
    self.medio_banos = 0
    self.seguridad_privada = 'No'
    self.ubicacion = ""
    self.url = ""
    self.descripcion = ""

#Función de obtención de los números del texto
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
# Función para extraer números de un texto
#def obtener_numero_de_texto(texto, entero=False):
#    match = re.search(r'\d+', texto)
#    if match:
#        return int(match.group()) if entero else float(match.group())
#    return None
  

def obtener_datos(soup: BeautifulSoup):
  contenedor_principal = soup.find('div', class_='adform__detail')

  # Datos
  datos = Lamudi()
  
  # Título
  try:
    titulo_html = contenedor_principal.find('div', class_='main-title')

    if titulo_html:
      datos.propiedad = titulo_html.text.strip()
  except:
    log.warn("Propiedad sin título")
  
  # Ubicación

  try:
    html = contenedor_principal.find('div', class_='view-map__text')

    if html:
      ubicacion = html.text.strip().replace("\n", "").replace("\r", "")
      datos.ubicacion = re.sub(' +', ' ', ubicacion)
  except:
    log.warn("Propiedad sin ubicación")
  
  # Precio

  try:
    html = contenedor_principal.find('div', class_='prices-and-fees__price')

    if html:
      datos.precio = obtener_numero_de_texto(html.text)
      datos.denominacion = DENOMINATION_USD if "US" in html.text else DENOMINATION_MXN
  except:
    log.warn("Propiedad sin precio")



  # M2, Recamaras, Medio baños, baños

  caracteristicas_html = None

  try:
    caracteristicas_html = contenedor_principal.find_all('div', class_='details-item-value')
  except:
    log.warn("Propiedad sin caracteristicas")
  
#  if caracteristicas_html:
#    for caracteristica in caracteristicas_html:
#      text = caracteristica.text
#      value = obtener_numero_de_texto(text, True)
#      if 'm²' in text:
#        datos.metros_construido = value
#      elif 'recámara' in text:
#        datos.recamaras = value
#      elif 'medio baño' in text:
#        datos.medio_banos = value
#      elif 'baño' in text:
#        datos.banos = value

# Función de búsqueda singular o plural
  if caracteristicas_html:
    for caracteristica in caracteristicas_html:
        text = caracteristica.text.lower()  # Convertir a minúsculas para una comparación más fácil
        value = obtener_numero_de_texto(text, True)
        
        if 'm²' in text:
            datos.metros_construido = value
        elif 'recámara' in text or 'recámaras' in text:
            datos.recamaras = value
        elif 'medio baño' in text or 'medio baños' in text:
            datos.medio_banos = value
        elif 'baño' in text or 'baños' in text:
            datos.banos = value

  # Tipo de casa

  try:
    html = contenedor_principal.find('div', class_="property-type")

    if html:
      datos.tipo = html.find("span", class_="place-features__values").text.strip()
  except:
    log.warn("Propiedad sin tipo de casa")

  # Metros construidos

  if datos.metros_construido <= 0:
    try:
      html = contenedor_principal.find('div', class_="floor-area")

      if html:
        datos.metros_construido = obtener_numero_de_texto(html.find("span", class_="place-features__values").text, True)
    except:
      log.warn("Propiedad metros construidos")

  # Metros totales

  try:
    html = contenedor_principal.find('div', class_="plot-area")

    if html:
      datos.metros_total = obtener_numero_de_texto(html.find("span", class_="place-features__values").text, True)
  except:
    log.warn("Propiedad sin metros totales")

  # Estacionamientos

  try:
    facilities = contenedor_principal.find_all('div', class_='facilities__item')

    if facilities:
      for facility in facilities:
        text = facility.text

        if 'Garaje' in text:
          datos.estacionamientos = 1
  except:
    log.warn("Propiedad sin estacionamientos")

  # Tiempo de publicación

  try:
    html = contenedor_principal.find('div', class_="date")

    if html:
      date = html.text.split(" - ")[0]

      if "Hace" in date:
          now = datetime.now()
          datos.tiempo_de_publicacion = now.strftime("%m/%d/%Y")
      else:
        datos.tiempo_de_publicacion = date.strip()
  except:
    log.warn("Propiedad sin tiempo de publicación")

  try:
    html = contenedor_principal.find('div', id="description-text")

    if html:
      datos.descripcion = html.text.strip().replace("\n", "").replace("\r", "")
  except:
    log.warn("Propiedad sin descripcion")

  return datos