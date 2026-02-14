from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# ------------------ Configuración Selenium ------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
driver.get("https://normativa.udea.edu.co/Documentos/Consultar")

wait = WebDriverWait(driver, 25)

# ------------------ Click en "Buscar" ------------------
btn = wait.until(EC.element_to_be_clickable((By.ID, "btnbuscar")))
driver.execute_script("arguments[0].scrollIntoView(true);", btn)
btn.click()

# Esperar a que aparezcan filas de resultados iniciales
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))

# ------------------ Función para extraer una página ------------------
def extraer_pagina():
    """
    Lee todas las filas visibles de #tblresultados y devuelve
    una lista de diccionarios con las claves requeridas.
    """
    resultados = []
    filas = driver.find_elements(By.CSS_SELECTOR, "#tblresultados tbody tr")
    for fila in filas:
        celdas = fila.find_elements(By.TAG_NAME, "td")
        if len(celdas) < 6:
            continue

        # Extraer número (texto) y el link al documento
        numero_link = celdas[0].find_element(By.TAG_NAME, "a")
        numero_texto = numero_link.text.strip()

        # El atributo href trae: javascript:verdocumento('35029998', '', '');
        href = numero_link.get_attribute("href")
        doc_id = href.split("verdocumento('")[1].split("'")[0]
        link_documento = f"https://normativa.udea.edu.co/Documentos/VerDocumento/{doc_id}"

        item = {
            "numero":               numero_texto,
            "fecha_expedicion":     celdas[1].text.strip(),
            "entrada_vigencia":     celdas[2].text.strip(),
            "medio_publicacion":    celdas[3].text.strip(),
            "resuelve":             celdas[4].text.strip(),
            "normas_relacionadas":  celdas[5].text.strip(),
            "link_documento":       link_documento,
        }
        resultados.append(item)
    return resultados

# ------------------ Recorrer primeras 9 páginas ------------------
MAX_PAGINAS = 9
datos = []

for pagina in range(1, MAX_PAGINAS + 1):
    print(f"Extrayendo página {pagina}...")

    try:
        fila_ref = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#tblresultados tbody tr:first-child")
        ))
    except:
        fila_ref = None

    driver.execute_script(f"buscar({pagina});")

    if fila_ref is not None:
        try:
            wait.until(EC.staleness_of(fila_ref))
        except:
            pass

    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))
    datos.extend(extraer_pagina())

driver.quit()

# ------------------ Guardar en Excel ------------------
df = pd.DataFrame(datos, columns=[
    "numero", "fecha_expedicion", "entrada_vigencia",
    "medio_publicacion", "resuelve", "normas_relacionadas", "link_documento"
])
df.to_excel("documentos_udea.xlsx", index=False)
print(f"Guardado {len(df)} filas en 'documentos_udea.xlsx'")