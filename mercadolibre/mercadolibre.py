from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import pandas as pd
import os
import json
import logging as log

# Inicializar el registro de eventos
log.basicConfig(level=log.INFO, filename='scraper_log.txt')

# Función para obtener las opciones de Chrome
def get_chrome_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("useAutomationExtension=False")
    chrome_options.add_argument("excludeSwitches=['enable-automation']")
    return chrome_options

# URL base y número total de páginas
base_url = "https://inmuebles.mercadolibre.com.mx/casas/pachuca-hidalgo_Desde_289_NoIndex_True"
total_pages =9
# Listas para almacenar datos
all_property_urls = []
viviendas_erroneas = []
datos_de_viviendas = []

# Obtener opciones de Chrome
options = get_chrome_options()

def normalizar(variable):
    variable = variable.replace("á", "a")
    variable = variable.replace("é", "e")
    variable = variable.replace("í", "i")
    variable = variable.replace("ó", "o")
    variable = variable.replace("ú", "u")
    variable = variable.replace("ñ", "n")
    variable = variable.replace("ü", "u")
    variable = variable.replace("m²", "m2")
    return variable

# Función para extraer los datos de la propiedad
def extraer_datos_propiedad(html):
    try:
        titulo = html.find('h1', class_='ui-pdp-title').text.strip()
        titulo = normalizar(titulo)
    except:
        titulo = "Propiedad sin título"
    try:
        estatus =  html.find('span', class_='ui-pdp-subtitle').text.strip()
        estatus = normalizar(estatus)
    except:
        estatus = "Propiedad sin estatus"
    try:
        tiempo_de_publicado =  html.find('p', class_='ui-pdp-header__bottom-subtitle').text.strip()
        tiempo_de_publicado = normalizar(tiempo_de_publicado)
    except:
        tiempo_de_publicado = "Propiedad sin tiempo de publicado"
    try:
        publicado_por =  html.find('p', class_='ui-pdp-seller-validated__title').text.strip()
        publicado_por = normalizar(publicado_por)
    except:
        publicado_por = "publicacion sin autor"
    try:
        denominacion = html.find('span', class_='andes-money-amount__currency-symbol').text.strip()
        denominacion = normalizar(denominacion)
    except:
        denominacion = "Propiedad sin precio"
    try:
        precio = html.find('span', class_='andes-money-amount__fraction').text.strip()
        precio = normalizar(precio)
    except:
        precio = "Propiedad sin precio"
    try:
        detalles = html.find_all('span', class_='ui-pdp-label')
        metros_totales = detalles[0].text.strip() if len(detalles) > 0 else "Propiedad sin metros totales"
        metros_totales = normalizar(metros_totales)
        recamaras = detalles[1].text.strip() if len(detalles) > 1 else "Propiedad sin recamaras"
        recamaras = normalizar(recamaras)
        baños = detalles[2].text.strip() if len(detalles) > 2 else "Propiedad sin baños"
        baños = normalizar(baños)
    except:
        metros_totales = "Propiedad sin metros totales" 
        recamaras = "Propiedad sin recamaras"
        baños = "Propiedad sin baños"
    try:
        ubicacion = html.find_all('div', class_='ui-pdp-media__body')[6].text.strip()
        ubicacion = ubicacion.replace("Ver información de la zona","")
        ubicacion = normalizar(ubicacion)
    except IndexError:
        ubicacion = "Propiedad sin ubicación"
    try:
        descripcion = html.find('p', class_='ui-pdp-description__content').text.strip()
        descripcion = normalizar(descripcion)
    except:
        descripcion = "Propiedad sin descripcion"
        

    caracteristicas_dict = {
        'Cantidad de pisos:': 'sin dato',
        'Asador:': 'sin dato',
        'Estacionamientos:': 'sin dato',
        'Con condominio cerrado:': 'sin dato',
        'Jardin:': 'sin dato',
        'Alberca:': 'sin dato',
        'Antiguedad:': 'sin dato'
    }

    try:
        detalles = html.find_all('p', class_='ui-pdp-family--REGULAR ui-vpp-highlighted-specs__key-value__labels__key-value')
        for detalle in detalles:
            nombre = normalizar(detalle.find('span',class_='ui-pdp-family--REGULAR').text.strip())
            valor = normalizar(detalle.find('span', class_='ui-pdp-family--SEMIBOLD').text.strip())
            for caracteristica in caracteristicas_dict:
                if caracteristica in nombre:
                    caracteristicas_dict[caracteristica] = valor
    except:
        pass

    return {
        'titulo': titulo,
        'estatus': estatus,
        'tiempo_de_publicado': tiempo_de_publicado,
        'publicado_por': publicado_por,
        'denominacion': denominacion,
        'precio': precio,
        'metros_totales': metros_totales,
        'recamaras': recamaras,
        'banos': baños,
        **caracteristicas_dict,
        'ubicacion': ubicacion,
        'descripcion': descripcion
    }

# Raspar URLs de propiedades
driver = None
try:
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    for page_number in range(1, total_pages + 1):
        page_url = base_url + f"_Desde_{(page_number - 1) * 48}"
        driver.get(page_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "ui-search-layout__item")))
        propiedades = driver.find_elements(By.CLASS_NAME, "ui-search-layout__item")

        for propiedad in propiedades:
            try:
                url = propiedad.find_element(By.XPATH, ".//a").get_attribute('href')
                log.info(f"URL de la propiedad encontrada: {url}")
                all_property_urls.append(url)
            except Exception as ex:
                log.warning(f"Error al obtener la URL de la propiedad: {str(ex)}")
except Exception as e:
    log.error(f"Error durante el raspado de las URLs: {e}")
finally:
    if driver:
        try:
            driver.quit()
        except Exception as e:
            log.error(f"Error al cerrar el navegador después de raspar las URLs: {e}")

# Procesar cada URL de propiedad
driver = None
try:
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    for url in all_property_urls:
        driver.get(url)
        codigo_html = bs(driver.page_source, 'html.parser')

        try:
            log.info(f"Extrayendo datos de: {url}")
            # Extraer los datos de la propiedad
            propiedad = extraer_datos_propiedad(codigo_html)
            propiedad['url'] = url
            datos_de_viviendas.append(propiedad)
        except Exception as ex:
            log.warning(f"Error al extraer datos de {url}: {str(ex)}")
            viviendas_erroneas.append(url)
except Exception as e:
    log.error(f"Error durante el procesamiento de las propiedades: {e}")
finally:
    if driver:
        try:
            driver.quit()
        except Exception as e:
            log.error(f"Error al cerrar el navegador después de procesar las propiedades: {e}")

# Guardar datos en CSV
nombre_archivo = "./datos/PachucaCasas_MercadoLibre_Agosto2024.csv"
try:
    if datos_de_viviendas:
        df = pd.DataFrame(datos_de_viviendas)
        # Mover la columna 'url' al final del DataFrame
        df = df[[col for col in df if col not in ['ubicacion', 'descripcion', 'url']] + ['ubicacion', 'descripcion', 'url']]
        
        if not os.path.isfile(nombre_archivo):
            df.to_csv(nombre_archivo, index=False, encoding='utf-8')
            log.info(f"CSV creado en: {nombre_archivo}")
        else:
            df.to_csv(nombre_archivo, mode='a', header=False, index=False, encoding='utf-8')
            log.info(f"Datos agregados al CSV en: {nombre_archivo}")
    else:
        log.warning("No se encontraron datos de viviendas para guardar en el CSV.")
except Exception as e:
    log.error(f"Error al guardar datos en el CSV: {e}")

# Guardar errores en un archivo JSON
error_file_path = "./datos/viviendas_errorneas.json"
try:
    if viviendas_erroneas:
        with open(error_file_path, 'w', encoding='utf-8') as f:
            json.dump(viviendas_erroneas, f)
            log.info(f"Errores guardados en JSON en: {error_file_path}")
    else:
        log.warning("No se encontraron viviendas con errores para guardar en el archivo JSON.")
except Exception as e:
    log.error(f"Error al guardar errores en el archivo JSON: {e}")

log.info("Raspado completo.")










