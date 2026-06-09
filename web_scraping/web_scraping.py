from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

URL = "https://normativa.udea.edu.co/Documentos/Consultar"

# ------------------ Configuración Selenium ------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 20)


# ------------------ FUNCIÓN ROBUSTA ANTI-STALE ------------------
def extraer_tabla(tipo_nombre):
    resultados = []

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))
        filas = driver.find_elements(By.CSS_SELECTOR, "#tblresultados tbody tr")
    except:
        return resultados

    for i in range(len(filas)):
        try:
            filas = driver.find_elements(By.CSS_SELECTOR, "#tblresultados tbody tr")
            fila = filas[i]
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

        except:
            continue

    return resultados


# ------------------ Tipos de documento ------------------
tipos = [
    ("01", "ACTAS"),
    ("02", "ACUERDOS"),
    ("23", "RESOLUCIONES")
]

datos_totales = []

# ------------------ BUCLE PRINCIPAL ------------------
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

        # ------------------ PAGINACIÓN INTELIGENTE ------------------
        pagina = 1

        while True:
            print(f"      Página {pagina}")

            datos_totales.extend(extraer_tabla(nombre))

            # Guardar contenido actual
            try:
                contenido_actual = driver.find_element(By.CSS_SELECTOR, "#tblresultados tbody").text
            except:
                break

            # Ir a siguiente página
            try:
                driver.execute_script(f"buscar({pagina + 1});")
                time.sleep(1.5)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))
            except:
                break

            # Comparar contenido
            try:
                contenido_nuevo = driver.find_element(By.CSS_SELECTOR, "#tblresultados tbody").text
            except:
                break

            # Si no cambia → última página
            if contenido_actual == contenido_nuevo:
                print("      Última página alcanzada")
                break

            pagina += 1


driver.quit()

# ------------------ Guardar Excel ------------------
df = pd.DataFrame(datos_totales)
df.to_excel("documentos_udea_2004_2024.xlsx", index=False)

print(f"\nTOTAL REGISTROS: {len(df)}")