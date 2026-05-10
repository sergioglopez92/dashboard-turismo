import pandas as pd
import os
import re

ARCHIVOS_CSV = ["results1.csv", "results2.csv"]
ARCHIVO_EXCEL = "Resultados_Airbnb.xlsx"

def limpiar_texto(texto):
    if not isinstance(texto, str):
        return ""
    
    # --------------- 1. CODIFICACIÓN ---------------
    correcciones = {
        'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
        'Ã±': 'ñ', 'Ã': 'Á', 'â‚¬': '€', 'Â': ' ', ' ': ' '
    }
    for mal, bien in correcciones.items():
        texto = texto.replace(mal, bien)
        
    texto = texto.lower()

    # --------------- 2. LIMPIEZA DE RUIDO ---------------
    patrones_a_eliminar = [
        r'del \d{1,2} al \d{1,2} [a-z]{3} \d{1,2}[–-]\d{1,2} [a-z]{3}', # Borra fechas
        r'valoración media de.*?\(\d+\)', # Borra bloque de valoraciones
        r'\d+\s*evaluaciones\s+\d+\s+\d+\s+estrellas\s+valoración.*?(?:experiencia|anfitrión)?', # Otro formato de valoraciones
        r'de los mejores anuncios',
        r'recomendación del viajero',
        r'anfitrión (particular|profesional)',
        r'consulta el desglose del precio',
        r'cancelación gratuita',
        r'\d+\s*€.*?en total',
        r'\d+\s*€',
        r'[,·]',
        r'[\n\r]+',
        # Borra camas y dormitorios porque YA los tienes en las columnas numéricas originales
        r'\d+\s*dormitorios?',  
        r'\d+\s*(camas?|literas?|sofás?\s*camas?)(?:\s+(dobles?|individuales?|«queen»|king))?', 
        r'\d+\.\s*\d+\.' # Colas numéricas residuales
    ]
    
    for patron in patrones_a_eliminar:
        texto = re.sub(patron, ' ', texto)

    # Elimina repeticiones exactas de palabras útiles para que no ensucian pero sigan ahí
    texto = re.sub(r'superanfitrión superanfitrión', 'superanfitrión', texto)
    texto = re.sub(r'alojamiento nuevo nuevo', 'alojamiento nuevo', texto)

    # Quita espacios múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def convertir_a_excel():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    print(f"⏳ Leyendo datos de: {ARCHIVOS_CSV}")
    
    try:
        # Leemos y combinamos los CSVs
        dfs = []
        for archivo in ARCHIVOS_CSV:
            ruta_csv = os.path.join(BASE_DIR, archivo)
            if os.path.exists(ruta_csv):
                df_temp = pd.read_csv(ruta_csv)
                print(f"   📥 {archivo} leído. Filas: {len(df_temp)}")
                dfs.append(df_temp)
        
        if not dfs:
            print("❌ Error: No se encontró ningún archivo CSV.")
            return

        # Juntamos todo de golpe y borramos duplicados
        df = pd.concat(dfs, ignore_index=True)
        print(f"   🔄 Filas totales unidas (antes de limpiar): {len(df)}")
        df = df.drop_duplicates()
        print(f"   ✅ Filas únicas reales (tras borrar repetidas): {len(df)}")
        
        # --------------- 3. ORDEN ---------------
        if "checkin_date" in df.columns and "city" in df.columns and "id" in df.columns:
            df = df.sort_values(by=["city", "id", "checkin_date"])

        # --------------- 4. CORRECIÓN VALORES VACÍOS ---------------
        print("🗺️ Rellenando distancias al centro faltantes...")
        if 'dist_centro_km' in df.columns and 'id' in df.columns:
            # Agrupa por ciudad e ID y copia el valor numérico (ignorando vacíos) a todas las filas del mismo alojamiento
            df['dist_centro_km'] = df.groupby(['city', 'id'])['dist_centro_km'].transform('max')
        
        print("🧹 Limpiando textos y corrigiendo caracteres...")

        print("🧹 Limpiando textos y corrigiendo caracteres...")
        
        # --------------- 5. EXTRACCIÓN DE CARACTERÍSTICAS ---------------
        # Detecta la columna con el texto largo
        col_texto = 'texto_completo' if 'texto_completo' in df.columns else 'raw_text'
        
        # Crea de una columna limpia para revisión
        df['texto_limpio'] = df[col_texto].apply(limpiar_texto)

        print("🔍 Extrayendo características...")
        # Crea columnas booleanas (1 o 0)
        df['tiene_wifi'] = df['texto_limpio'].str.contains('wifi', na=False).astype(int)
        df['tiene_aire_acond'] = df['texto_limpio'].str.contains('aire acondicionado', na=False).astype(int)
        df['tiene_piscina'] = df['texto_limpio'].str.contains('piscina', na=False).astype(int)
        df['tiene_parking'] = df['texto_limpio'].str.contains('aparcamiento|parking|garaje', na=False, regex=True).astype(int)
        df['tiene_terraza_balcon'] = df['texto_limpio'].str.contains('terraza|balcón|balcon', na=False, regex=True).astype(int)
        df['tiene_patio'] = df['texto_limpio'].str.contains('patio', na=False).astype(int)
        df['tiene_vistas'] = df['texto_limpio'].str.contains('vistas', na=False).astype(int)
        df['es_superanfitrion'] = df['texto_limpio'].str.contains('superanfitrión', na=False).astype(int)
        df['es_nuevo'] = df['texto_limpio'].str.contains('alojamiento nuevo', na=False).astype(int)
        df['es_casa_rural'] = df['texto_limpio'].str.contains('casa rural', na=False).astype(int)
        df['es_hotel'] = df['texto_limpio'].str.contains('hotel', na=False).astype(int)
        df['es_solo_habitacion'] = df['texto_limpio'].str.contains('habitaci[óo]n', na=False, regex=True).astype(int)

        print("✨ Estructurando columnas y convirtiendo a Excel...")
        
        # Exporta a formato nativo de Excel sin la columna de numeración (index=False)
        df.to_excel(ARCHIVO_EXCEL, index=False, engine='openpyxl')
        
        print(f"✅ ¡Éxito! Archivo guardado como: {ARCHIVO_EXCEL}")
        
    except FileNotFoundError:
        print(f"❌ Error: Faltan archivos CSV.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    convertir_a_excel()