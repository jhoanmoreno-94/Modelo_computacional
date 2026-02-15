from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

URL = "https://normativa.udea.edu.co/Documentos/Consultar"

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)

def extraer_tabla(tipo_nombre):
    resultados = []
    filas = driver.find_elements(By.CSS_SELECTOR, "#tblresultados tbody tr")

    for fila in filas:
        celdas = fila.find_elements(By.TAG_NAME, "td")
        if len(celdas) < 6:
            continue

        resultados.append({
            "tipo_documento": tipo_nombre,
            "numero": celdas[0].text.strip(),
            "fecha_expedicion": celdas[1].text.strip(),
            "entrada_vigencia": celdas[2].text.strip(),
            "medio_publicacion": celdas[3].text.strip(),
            "resuelve": celdas[4].text.strip(),
            "normas_relacionadas": celdas[5].text.strip(),
        })

    return resultados


tipos = [
    ("01", "ACTAS"),
    ("02", "ACUERDOS"),
    ("23", "RESOLUCIONES")
]

datos_totales = []

for valor, nombre in tipos:
    print(f"\n===== {nombre} =====")

    for anio in range(2004, 2025):
        print(f"Año: {anio}")

        # Reiniciar página
        driver.get(URL)

        # Seleccionar tipo
        select_element = wait.until(EC.presence_of_element_located((By.ID, "tipodocumento")))
        Select(select_element).select_by_value(valor)

        # Escribir año
        fecha_input = driver.find_element(By.ID, "fecha")
        fecha_input.clear()
        fecha_input.send_keys(str(anio))

        # Buscar
        driver.find_element(By.ID, "btnbuscar").click()

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))
        except:
            print("   Sin resultados")
            continue

        # Extraer primera página
        datos_totales.extend(extraer_tabla(nombre))

        # Detectar número de páginas
        try:
            paginacion = driver.find_elements(By.CSS_SELECTOR, ".pagination li a")
            paginas = []

            for p in paginacion:
                texto = p.text.strip()
                if texto.isdigit():
                    paginas.append(int(texto))

            max_pagina = max(paginas) if paginas else 1

        except:
            max_pagina = 1

        print(f"   Total páginas detectadas: {max_pagina}")

        # Límite de seguridad
        max_pagina = min(max_pagina, 1500)

        # Recorrer páginas restantes
        for pagina in range(2, max_pagina + 1):
            print(f"      Página {pagina}")

            try:
                fila_ref = driver.find_element(By.CSS_SELECTOR, "#tblresultados tbody tr:first-child")
                driver.execute_script(f"buscar({pagina});")
                wait.until(EC.staleness_of(fila_ref))
                time.sleep(1)
                datos_totales.extend(extraer_tabla(nombre))
            except:
                print("      Error cambiando página")
                break


driver.quit()

df = pd.DataFrame(datos_totales)
df.to_excel("documentos_udea_2004_2024.xlsx", index=False)

print(f"\nTOTAL REGISTROS: {len(df)}")