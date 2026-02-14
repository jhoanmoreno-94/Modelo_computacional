from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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

# ------------------ Función para extraer tabla ------------------
def extraer_tabla(tipo_nombre):
    resultados = []
    filas = driver.find_elements(By.CSS_SELECTOR, "#tblresultados tbody tr")

    for fila in filas:
        celdas = fila.find_elements(By.TAG_NAME, "td")
        if len(celdas) < 6:
            continue

        item = {
            "tipo_documento": tipo_nombre,
            "numero": celdas[0].text.strip(),
            "fecha_expedicion": celdas[1].text.strip(),
            "entrada_vigencia": celdas[2].text.strip(),
            "medio_publicacion": celdas[3].text.strip(),
            "resuelve": celdas[4].text.strip(),
            "normas_relacionadas": celdas[5].text.strip(),
        }

        resultados.append(item)

    return resultados


# ------------------ Tipos de documento ------------------
tipos = [
    ("01", "ACTAS"),
    ("02", "ACUERDOS"),
    ("23", "RESOLUCIONES")
]

datos_totales = []

# ------------------ Bucle principal ------------------
for valor, nombre in tipos:
    print(f"\n===== Procesando {nombre} =====")

    for anio in range(2004, 2025):
        print(f"  Año: {anio}")

        # Seleccionar tipo documento
        select_element = wait.until(EC.presence_of_element_located((By.ID, "tipodocumento")))
        select = Select(select_element)
        select.select_by_value(valor)

        # Limpiar y escribir año en campo fecha
        fecha_input = driver.find_element(By.ID, "fecha")
        fecha_input.clear()
        fecha_input.send_keys(str(anio))

        # Click en buscar
        btn = wait.until(EC.element_to_be_clickable((By.ID, "btnbuscar")))
        btn.click()

        # Esperar resultados
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#tblresultados tbody tr")))
        except:
            print("    No hay resultados.")
            continue

        # -------- Recorrer páginas del año --------
        pagina = 1
        while True:
            print(f"    Página {pagina}")

            datos_totales.extend(extraer_tabla(nombre))

            # Intentar ir a siguiente página
            try:
                fila_ref = driver.find_element(By.CSS_SELECTOR, "#tblresultados tbody tr:first-child")
                driver.execute_script(f"buscar({pagina + 1});")
                wait.until(EC.staleness_of(fila_ref))
                pagina += 1
            except:
                break

driver.quit()

# ------------------ Guardar Excel ------------------
df = pd.DataFrame(datos_totales, columns=[
    "tipo_documento",
    "numero",
    "fecha_expedicion",
    "entrada_vigencia",
    "medio_publicacion",
    "resuelve",
    "normas_relacionadas"
])

df.to_excel("documentos_udea_2004_2024.xlsx", index=False)

print(f"\n Total registros guardados: {len(df)}")