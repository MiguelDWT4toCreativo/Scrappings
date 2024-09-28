from time import sleep
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome
import pandas as pd
import numpy as np
import os
import json
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import helpers as hp
import logging as log

CHROME_VERSION = 129

url_base = "https://www.inmuebles24.com"
base_path = "inmuebles-en-venta-en-tulancingo-de-bravo"
ext = ".html"
url_wo_ext = f"{url_base}/{base_path}"
url = f"{url_wo_ext}{ext}"
nombre_archivo = f"datos/Tulancingo_Inmuebles_Inmuebles24_Agosto2024.csv"
log.basicConfig(level = log.INFO)
datos_de_viviendas = []
viviendas_erroneas = []
urls = []

navegador = Chrome(use_subprocess=True, version_main=CHROME_VERSION)

navegador.get(url)
sleep(3)
contenedor_propiedades = navegador.find_element(By.CLASS_NAME, "postings-container")

pagina_previa = None

for i in range(0, 1000):
  for y in range(0, 20):
    try:
      loader = contenedor_propiedades.find_element(By.XPATH, "//img[contains(@alt, 'loading...')]")
    except:
      break

    if loader == None:
      break

    sleep(1)
  sleep(1)
  
  pagina_actual = navegador.current_url

  if pagina_actual != pagina_previa:
    pagina_previa = pagina_actual
    propiedades = []

    try:
      propiedades = contenedor_propiedades.find_elements(By.XPATH, "//div[contains(@data-qa, 'posting')]")
    except:
      log.info("Final de los resultados")

    for propiedad in propiedades:
      try:
        url_propiedad = url_base + propiedad.get_attribute("data-to-posting")
        urls.append(url_propiedad)
      except Exception as ex:
        log.warn("No se pudo obtener la URL de esta propiedad, mensaje: " + str(ex))

  boton_siguiente = None

  try:
        boton_siguiente = navegador.find_element(By.CSS_SELECTOR, '[data-qa="PAGING_NEXT"]')
  except NoSuchElementException:
        log.info("Final de los resultados, terminando scrapping.")
        break

  if not boton_siguiente:
        log.info("Botón 'Siguiente' no encontrado. Terminando el scraping.")
        break

  try:
    cookies = navegador.find_element( By.CLASS_NAME, 'CookiesPolicyBanner-module__cookiesContainer___H0Vq')
    if cookies:
      navegador.execute_script("arguments[0].remove();", cookies)
  except:
    log.debug("No botón de coockies")

  boton_siguiente.click()

navegador.close()

log.info(f"Total de propiedades: {len(urls)}")

navegador_2 = Chrome(use_subprocess=True, version_main=CHROME_VERSION)

np_urls = np.array(urls)
subgrupos = np.array_split(np_urls, 20)

for subgrupo in subgrupos:
  datos_de_viviendas = []
  for url in subgrupo:
    navegador_2.get(url)

    codigo_html = bs(navegador_2.page_source, 'html.parser')

    try:
      log.info(f"Intentando obtener datos de: {url}")
      inmuebles = hp.obtener_datos(codigo_html)
      inmuebles.url = url
      datos_de_viviendas.append(inmuebles)
    except Exception as ex:
      log.error(f"Error tratando de obtener los datos, mensaje {str(ex)}")
      viviendas_erroneas.append(url)

  df = pd.DataFrame([vars(vivienda) for vivienda in datos_de_viviendas])

  if not os.path.isfile(nombre_archivo):
    df.to_csv(nombre_archivo, index=False, encoding='utf-8')
  else:
    df.to_csv(nombre_archivo, mode='a', header=False, index=False)

navegador_2.close()

with open('viviendas_errorneas.json', 'w') as f:
  json.dump(viviendas_erroneas, f)
