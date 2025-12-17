import pandas as pd
import numpy as np
import io
import re
import os

from google.colab import drive
drive.mount('/content/drive')
from google.colab import files

import json

import matplotlib.pyplot as plt
from matplotlib.pylab import *

from scipy.optimize import root

import sympy as sp

from datetime import datetime
print("\n" + "="*70)
print("CARGA DE LIBRERIAS COMPLETA")

# ==============================================================================
#                 FUNCIONES AUXILIARES CARGA DE ARCHIVOS
# ==============================================================================

# ----------------------------- Archivos RPT ----------------------------------#


def procesar_k0s_independiente(ruta_entrada, ruta_salida):
    """Lee el K0S y genera un Excel independiente."""
    metadata = []
    try:
        with open(ruta_entrada, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= LINES_TO_READ_K0S: break
                cleaned_line = line.strip()
                tokens = re.split(r'\s+', cleaned_line) if cleaned_line else ['']
                metadata.append(tokens)
        df = pd.DataFrame(metadata)
        df.to_excel(ruta_salida, index=False, header=False, na_rep='')
        return True
    except Exception as e:
        print(f" [K0S] Error: {e}")
        return False

def limpiar_nombre(texto):
    """Normaliza nombres para comparación (quita guiones, espacios, mayúsculas)."""
    if pd.isna(texto): return ""
    # Convierte a string, mayúsculas, quita guiones y espacios
    return str(texto).upper().replace('-', '').replace(' ', '').strip()



# ----------------------------- Archivos k0s ----------------------------------#

# --------------------------------------------------------------------------
# FUNCIÓN QUE CONVIERTE ARCHIVO .k0s EN .xlsx
# Extrae 10 primeras filas
# CONTIENE fecha, hora de medición, t_vivo y t_real

def extract_and_tokenize_metadata(input_k0s_file, output_xlsx_file, num_lines):
    """
    Extrae las primeras 'num_lines' de un archivo .k0s, separa el contenido por
    espacios, lo exporta a un archivo .xlsx y retorna el DataFrame.
    """
    metadata = []

    try:
        # Asegurarse de que el archivo existe primero
        if not os.path.exists(input_k0s_file):
             print(f"Error: El archivo de entrada no se encontró: {input_k0s_file}")
             return None

        print(f"Leyendo las primeras {num_lines} líneas de: {input_k0s_file}...")

        with open(input_k0s_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break

                # 1. Limpieza de la línea
                cleaned_line = line.strip()

                # 2. Tokenización por Espacios (Usando Expresión Regular)
                if cleaned_line:
                    tokens = re.split(r'\s+', cleaned_line)
                else:
                    # Línea completamente vacía
                    tokens = ['']

                metadata.append(tokens)

        # 3. Crear DataFrame de Pandas
        df = pd.DataFrame(metadata)

        # 4. Guardar el DataFrame a Excel
        df.to_excel(output_xlsx_file,
                    index=False,
                    header=False,
                    na_rep='')

        print(f"Extracción de las primeras {num_lines} líneas exitosa.")
        print(f"Archivo de salida: **{output_xlsx_file}**")

        return df

    except FileNotFoundError:
        print(f"Error: El archivo de entrada no se encontró: {input_k0s_file}")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el proceso: {e}")
        return None

# --------------------------------------------------------------------------
# FUNCIÓN QUE EXTRAE LOS VALORES
# fecha, hora de medición, t_vivo y t_real
# --------------------------------------------------------------------------
def extraer_variables_clave(df):
    """
    Extrae elementos específicos por posición (índice de fila, índice de columna)
    y los asigna a variables específicas.
    """
    try:
        # Verificamos que el DataFrame tenga el tamaño suficiente para evitar errores
        # Necesitamos al menos índice 5 (6 filas) y columna 1 (2 columnas)
        if df is not None and df.shape[0] > 5 and df.shape[1] > 1:

            # Extracción usando iloc[fila, columna]
            f_med = df.iloc[3, 0]     # Elemento [3, 0]
            hora_med = df.iloc[3, 1]  # Elemento [3, 1]
            t_v = df.iloc[5, 0]       # Elemento [5, 0]
            t_r = df.iloc[5, 1]       # Elemento [5, 1]

            return f_med, hora_med, t_v, t_r
        else:
            print("Error: El DataFrame es demasiado pequeño o es None.")
            return None, None, None, None

    except Exception as e:
        print(f"Error al extraer variables: {e}")
        return None, None, None, None
