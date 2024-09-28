#!/usr/bin/env python3

from time import sleep
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import numpy as np
import os
import json
import helpers as hp
import logging as log

log.basicConfig(level=log.INFO)
url_base = "https://www.lamudi.com.mx"
base_path = "tlaxcala/huamantla/for-sale/?propertyTypeGroups=casa%2Cdepartamento"
ext = ""
url_wo_ext = f"{url_base}/{base_path}"
url = f"{url_wo_ext}{ext}"
nombre_archivo = "lamudi-TlaxcalaInmuebles_Agosto2024.csv"

datos_de_viviendas = []
viviendas_erroneas = []
urls = []

chrome_options = Options()
chrome_service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome()
#driver_path = 'C:/Users/Administrator/Downloads/chromedriver-win64 (3)/chromedriver.exe'
#service = Service(driver_path)
#driver = webdriver.Chrome(service=service)
#wait = WebDriverWait(driver,20) # Tiempo de espera en cargar

#navegador.get(url)
driver.get(url)
sleep(20)

pagina_previa = None

for i in range(0, 1000):
    try:
        contenedor_propiedades = driver.find_element(By.ID, "listings-content")
    except:
        log.info("No se pudo encontrar el contenedor de propiedades")
        driver.refresh()
        continue

    sleep(20)

    pagina_actual = driver.current_url
    if pagina_actual != pagina_previa:
        pagina_previa = pagina_actual
        propiedades = []
        try:
            propiedades = contenedor_propiedades.find_elements(By.CSS_SELECTOR, "a.snippet.js-snippet.normal")
        except:
            log.info("Final de los resultados")

        for propiedad in propiedades:
            try:
                url_propiedad = propiedad.get_attribute('href')
                if url_propiedad:
                    log.info(f"URL de propiedad: {url_propiedad}")
                    urls.append(url_propiedad)
                else:
                    log.warning("URL de propiedad es None")
            except Exception as ex:
                log.warning("No se pudo obtener la URL de esta propiedad, mensaje: " + str(ex))

    boton_siguiente = None

    try:
        boton_siguiente = driver.find_element(By.ID, 'pagination-next')
    except:
        log.info("Final de los resultados, terminando scrapping")

    if not boton_siguiente or not boton_siguiente.get_attribute("href"):
        break

    driver.get(boton_siguiente.get_attribute('href'))
    sleep(20)  # Seconds delay before navigating to the next page

driver.close()

log.info(f"Total de propiedades: {len(urls)}")

np_urls = np.array(urls)
subgrupos = np.array_split(np_urls, 20)

for subgrupo in subgrupos:
    sleep(20)  # Delay before opening a new browser instance
    driver_2 = webdriver.Chrome()
    #driver_2 = webdriver.Chrome(service=service)
    datos_de_viviendas = []

    for url in subgrupo:
        driver_2.get(url)

        try:
            WebDriverWait(driver_2, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "page__container"))
            )
            codigo_html = bs(driver_2.page_source, 'html.parser')
            log.info(f"Intentando obtener datos de: {url}")
            lamudi = hp.obtener_datos(codigo_html)
            lamudi.url = url
            datos_de_viviendas.append(lamudi)
        except Exception as ex:
            log.error(f"Error tratando de obtener los datos de {url}, mensaje: {str(ex)}")
            viviendas_erroneas.append(url)

    driver_2.close()

    df = pd.DataFrame([vars(vivienda) for vivienda in datos_de_viviendas])

    if not os.path.isfile(nombre_archivo):
        df.to_csv(nombre_archivo, index=False)
    else:
        df.to_csv(nombre_archivo, mode='a', header=False, index=False)

with open('viviendas_erroneas.json', 'w') as f:
    json.dump(viviendas_erroneas, f)
