from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from undetected_chromedriver import Chrome, ChromeOptions
import pandas as pd
import os
import json
import logging as log
import helpers as hp
import undetected_chromedriver as uc

# Initialize logging
log.basicConfig(level=log.INFO, filename='scraper_log.txt')

# Function to get ChromeOptions
def get_chrome_options():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("useAutomationExtension=False")
    chrome_options.add_argument("excludeSwitches=['enable-automation']")
    chrome_options.add_argument("--version-main=129")  # Set the Chrome version
    return chrome_options

# Base URL and total number of pages
base_url = "https://propiedades.com/mixquiahuala-de-juarez/casas-venta?pagina=1#remates=2"
total_pages = 1

# Lists to store data
all_property_urls = []
viviendas_erroneas = []
datos_de_viviendas = []

# Scrape property URLs
navegador = None
try:
    navegador = Chrome(options=get_chrome_options())
    navegador.maximize_window()
    for page_number in range(1, total_pages + 1):
        page_url = f"{base_url}?pagina={page_number}" if page_number > 1 else base_url
        navegador.get(page_url)
        WebDriverWait(navegador, 12).until(EC.presence_of_element_located((By.CLASS_NAME, "properties-cards")))
        propiedades = navegador.find_elements(By.CLASS_NAME, "pcom-property-card")

        for propiedad in propiedades:
            try:
                url = propiedad.find_element(By.XPATH, ".//meta[@itemprop='url']").get_attribute('content')
                log.info(f"Property URL found: {url}")
                all_property_urls.append(url)
            except Exception as ex:
                log.warning(f"Error obtaining property URL: {str(ex)}")
except Exception as e:
    log.error(f"Error during scraping URLs: {e}")
finally:
    if navegador:
        try:
            navegador.quit()
        except Exception as e:
            log.error(f"Error closing the browser after scraping URLs: {e}")

# Print all property URLs (for debugging)
log.info("All Property URLs:")
log.info(all_property_urls)

# Process each property URL
navegador = None
try:
    navegador = Chrome(options=get_chrome_options())
    navegador.maximize_window()
    for url in all_property_urls:
        navegador.get(url)
        codigo_html = bs(navegador.page_source, 'html.parser')

        try:
            log.info(f"Extracting data from: {url}")
            propiedad = hp.obtener_datos(codigo_html)  # Assuming this is your custom function
            propiedad.url = url
            datos_de_viviendas.append(propiedad)
        except Exception as ex:
            log.warning(f"Error extracting data from {url}: {str(ex)}")
            viviendas_erroneas.append(url)
except Exception as e:
    log.error(f"Error during processing properties: {e}")
finally:
    if navegador:
        try:
            navegador.quit()
        except Exception as e:
            log.error(f"Error closing the browser after processing properties: {e}")

# Print extracted data (for debugging)
log.info("Extracted Data:")
log.info(datos_de_viviendas)

# Save data to CSV
nombre_archivo = "C:/Users/IngeM/OneDrive/Escritorio/Scrapping Teseo/propiedades/datos/propiedades-PumasCU.csv"
try:
    if not os.path.isfile(nombre_archivo):
        df = pd.DataFrame([vars(vivienda) for vivienda in datos_de_viviendas])
        df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
        log.info(f"CSV created at: {nombre_archivo}")
    else:
        df = pd.DataFrame([vars(vivienda) for vivienda in datos_de_viviendas])
        df.to_csv(nombre_archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
        log.info(f"Data appended to CSV at: {nombre_archivo}")
except Exception as e:
    log.error(f"Error saving data to CSV: {e}")

# Save errors to a JSON file
error_file_path = "C:/Users/IngeM/OneDrive/Escritorio/Scrapping Teseo/propiedades/datos/viviendas_erroneas.json"
try:
    with open(error_file_path, 'w', encoding='utf-8') as f:
        json.dump(viviendas_erroneas, f, ensure_ascii=False, indent=4)
        log.info(f"Errors saved to JSON at: {error_file_path}")
except Exception as e:
    log.error(f"Error saving errors to JSON file: {e}")

log.info("Scraping complete.")