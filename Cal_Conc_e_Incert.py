# @title # Calculo de concentración e incertidumbre

# ==============================================================================
#                           CONFIGURACIÓN GENERAL
# ==============================================================================
#directorio_base = r'C:\Users\Yo\OneDrive\Documentos\PRUEBA'
directorio_base = "/content/drive/MyDrive/k0"

# --- Configuración para RPT ---
NOMBRE_BASE_DATOS_INFO = 'Base de datos.xlsx'
COLUMNA_BD_ENERGIA = 'EGKEV'           # Columna G (Energía BD)
COLUMNA_BD_NUCLIDO = 'NUCLIDES'        # Columna B (Nombre Nucleido BD)
TOLERANCIA_ENERGIA = 1.5
FILAS_A_OMITIR_RPT = 17
CODIFICACION = 'latin-1'

# --- Configuración para K0S ---
LINES_TO_READ_K0S = 10

# ==============================================================================
#                       FUNCIONES AUXILIARES
# =============================================================================


# ==============================================================================
#                 CARGA DE BASE DE DATOS (RPT)
# ==============================================================================
ruta_info_extra = os.path.join(directorio_base, NOMBRE_BASE_DATOS_INFO)
df_info_extra = None

print("--- INICIANDO SISTEMA DE DOBLE VALIDACIÓN (ENERGÍA + NOMBRE) ---")

if os.path.exists(ruta_info_extra):
    try:
        df_info_extra = pd.read_excel(ruta_info_extra)

        # 1. Verificar Columna Energía (G / EGKEV)
        if COLUMNA_BD_ENERGIA not in df_info_extra.columns:
            if len(df_info_extra.columns) > 6:
                df_info_extra.rename(columns={df_info_extra.columns[6]: COLUMNA_BD_ENERGIA}, inplace=True)

        # 2. Verificar Columna Nombre (B / NUCLIDES)
        if COLUMNA_BD_NUCLIDO not in df_info_extra.columns:
            if len(df_info_extra.columns) > 1: # La columna B es índice 1
                df_info_extra.rename(columns={df_info_extra.columns[1]: COLUMNA_BD_NUCLIDO}, inplace=True)

        # Limpiezas
        df_info_extra[COLUMNA_BD_ENERGIA] = pd.to_numeric(df_info_extra[COLUMNA_BD_ENERGIA], errors='coerce')
        df_info_extra.dropna(subset=[COLUMNA_BD_ENERGIA], inplace=True)

        # Pre-procesar nombres de la BD para búsqueda rápida
        df_info_extra['NOMBRE_LIMPIO_BD'] = df_info_extra[COLUMNA_BD_NUCLIDO].apply(limpiar_nombre)

        print(f" Base de Datos cargada. Columnas clave: Energía='{COLUMNA_BD_ENERGIA}', Nombre='{COLUMNA_BD_NUCLIDO}'")
    except Exception as e:
        print(f" Error grave en Base de Datos: {e}")
        df_info_extra = None
else:
    print(f" [AVISO] No se encontró '{NOMBRE_BASE_DATOS_INFO}'.")

# ==============================================================================
#                           BUCLE PRINCIPAL
# ==============================================================================
while True:
    print("\n" + "="*70)
    print(f"Directorio: {directorio_base}")

    nombre_input = input("Ingrese el nombre del archivo (Sin extensión): ").strip()
    if nombre_input.lower() in ('salir', 'exit', 'q'): break

    nombre_base = os.path.splitext(nombre_input)[0]

    # //////////////////////////////////////////////////////////////////////////
    #                           BLOQUE 1: GENERACIÓN EXCEL K0S
    # //////////////////////////////////////////////////////////////////////////
    nombre_k0s = nombre_base + '.k0s'
    ruta_k0s = os.path.join(directorio_base, nombre_k0s)
    ruta_salida_k0s = os.path.join(directorio_base, f"{nombre_base}_k0s.xlsx")

    print(f"\n--- 1. PROCESANDO K0S ({nombre_k0s}) ---")
    if os.path.exists(ruta_k0s):
        if procesar_k0s_independiente(ruta_k0s, ruta_salida_k0s):
            print(f" [OK] K0S generado: {os.path.basename(ruta_salida_k0s)}")
        else: print(" [X] Error generando K0S.")
    else: print(" [i] No existe archivo .k0s. Omitido.")

    # //////////////////////////////////////////////////////////////////////////
    #                           BLOQUE 2: GENERACIÓN EXCEL RPT
    # //////////////////////////////////////////////////////////////////////////
    nombre_rpt = nombre_base + '.RPT'
    ruta_rpt = os.path.join(directorio_base, nombre_rpt)

    print(f"\n--- 2. PROCESANDO RPT ({nombre_rpt}) ---")
    if not os.path.exists(ruta_rpt):
        print(f" [!] Archivo RPT no existe. Fin del ciclo."); continue

    # --- A. Selección Geometría ---
    nombre_ref_energia = ""
    while True:
        print(" Seleccione Tiempo RPT:")
        tipo = input("  [C]=Corta, [M]=Media, [L]=Larga: ").upper().strip()
        if tipo in ['C', 'M', 'L']:
            nombre_ref_energia = f'RDN_{tipo}.xlsx'
            break
        print("  Opción inválida.")

    # --- B. Carga Referencia ---
    try:
        ruta_ref = os.path.join(directorio_base, nombre_ref_energia)
        df_nuclidos = pd.read_excel(ruta_ref)
        col_en_excel = df_nuclidos.columns[1] # Asumimos col 1 es energía
        df_nuclidos[col_en_excel] = pd.to_numeric(df_nuclidos[col_en_excel], errors='coerce')
        df_nuclidos.dropna(subset=[col_en_excel], inplace=True)
    except Exception as e: print(f" Error cargando RDN: {e}"); continue

    # --- C. Rutas Salida RPT ---
    ruta_temp = os.path.join(directorio_base, f'{nombre_base}_TEMP.xlsx')
    ruta_verif = os.path.join(directorio_base, f'{nombre_base}_VERIFICADO.xlsx')
    ruta_final = os.path.join(directorio_base, f'{nombre_base}_FINAL_UNIFICADO.xlsx')

    # --- D. Lectura RPT ---
    try:
        cols_rpt = ['F/M', 'Peak_No', 'ROI_Start', 'ROI_End', 'Peak_Centroid',
                    'Energy_keV', 'Net_Peak_Area', 'Net_Area_Uncert', 'Continuum_Counts',
                    'Tentative_Nuclide', 'Info_Extra']

        df_rpt = pd.read_csv(ruta_rpt, sep=r'\s+', skiprows=FILAS_A_OMITIR_RPT, encoding=CODIFICACION,
                             names=cols_rpt, skipinitialspace=True, engine='python').dropna(how='all')

        # Ajustes de columnas
        df_rpt['Tentative_Nuclide'] = df_rpt['Tentative_Nuclide'].fillna('').astype(str)
        df_rpt['Info_Extra'] = df_rpt['Info_Extra'].fillna('').astype(str)

        # Unir Info Extra al nombre si existe
        mask = df_rpt['Info_Extra'] != ''
        if mask.any():
            df_rpt.loc[mask, 'Tentative_Nuclide'] = df_rpt.loc[mask, 'Tentative_Nuclide'] + " " + df_rpt.loc[mask, 'Info_Extra']
        df_rpt.drop(columns=['Info_Extra'], inplace=True)

        for col in ['Energy_keV', 'Net_Peak_Area']:
            df_rpt[col] = pd.to_numeric(df_rpt[col], errors='coerce')
        df_rpt.dropna(subset=['Energy_keV'], inplace=True)

    except Exception as e: print(f" Error leyendo RPT: {e}"); continue

    # --- E. Comparación Energías Y NOMBRES ---

    # 1. Buscar coincidencias por ENERGÍA
    def buscar_identidad(valor_pico):
        matches = df_nuclidos[
            (df_nuclidos.iloc[:,1] >= valor_pico - TOLERANCIA_ENERGIA) &
            (df_nuclidos.iloc[:,1] <= valor_pico + TOLERANCIA_ENERGIA)
        ]
        return ", ".join(matches.iloc[:,0].astype(str).tolist()) if not matches.empty else 'Desconocido'

    print(" Verificando energías...")
    df_rpt['Identidad_Verificada_Energia'] = df_rpt['Energy_keV'].apply(buscar_identidad)

    # 2. Verificar coincidencia de NOMBRE (Tentative vs Verificada)
    print(" Verificando nombres...")

    def comprobar_nombre_match(row):
        # Obtenemos el nombre que dio GENNIE (Tentative) y el que hallamos por energía (Verificada)
        nombre_tentativo = limpiar_nombre(row['Tentative_Nuclide'])
        nombre_verificado_energia = limpiar_nombre(row['Identidad_Verificada_Energia'])

        # Si no se encontró por energía, es falso
        if not nombre_verificado_energia or nombre_verificado_energia == 'DESCONOCIDO':
            return False

        # COMPROBACIÓN: ¿El nombre tentativo está dentro de los hallados por energía?
        if nombre_tentativo in nombre_verificado_energia:
            return True
        return False

    # Aplicamos la comprobación línea por línea
    df_rpt['COINCIDE_NOMBRE_Y_ENERGIA'] = df_rpt.apply(comprobar_nombre_match, axis=1)

    # 3. FILTRADO: Nos quedamos SOLO con los que coinciden
    df_verificado = df_rpt[df_rpt['COINCIDE_NOMBRE_Y_ENERGIA'] == True].copy()

    # Limpieza visual (borramos la columna booleana auxiliar)
    df_verificado.drop(columns=['COINCIDE_NOMBRE_Y_ENERGIA'], inplace=True)

    if not df_verificado.empty:
        df_verificado.to_excel(ruta_verif, index=False)
        print(f" [FILTRO] Se encontraron {len(df_verificado)} picos donde coinciden Energía y Nombre.")
    else:
        print(" [AVISO] Ningún pico cumplió la doble validación (Energía + Nombre). Saltando."); continue

    # --- F. CRUCE FINAL CON BASE DE DATOS EXTRA ---
    if df_info_extra is not None:
        print(" Realizando cruce final con Base de Datos...")
        filas_finales = []

        for _, row_rpt in df_verificado.iterrows():
            e_rpt = row_rpt['Energy_keV']

            # Buscamos en la BD general por energía
            candidatos_bd = df_info_extra[
                (df_info_extra[COLUMNA_BD_ENERGIA] >= e_rpt - TOLERANCIA_ENERGIA) &
                (df_info_extra[COLUMNA_BD_ENERGIA] <= e_rpt + TOLERANCIA_ENERGIA)
            ]

            if not candidatos_bd.empty:
                nombre_rpt_limpio = limpiar_nombre(row_rpt['Tentative_Nuclide'])

                for _, row_bd in candidatos_bd.iterrows():
                    nombre_bd_limpio = row_bd['NOMBRE_LIMPIO_BD']

                    # (Opcional) Triple validación: asegurar que la BD también hable del mismo elemento
                    if nombre_bd_limpio in nombre_rpt_limpio:
                        data_combinada = {**row_rpt.to_dict(), **row_bd.to_dict()}
                        if 'NOMBRE_LIMPIO_BD' in data_combinada: del data_combinada['NOMBRE_LIMPIO_BD']
                        filas_finales.append(data_combinada)

        if filas_finales:
            df_final = pd.DataFrame(filas_finales)
            # Reordenar columnas visualmente
            cols_prioridad = list(df_verificado.columns)
            cols_finales = cols_prioridad + [c for c in df_final.columns if c not in cols_prioridad]
            df_final = df_final[cols_finales]

            df_final.to_excel(ruta_final, index=False)
            print(f" [OK] Reporte FINAL generado: {os.path.basename(ruta_final)}")
        else:
            print(" [AVISO] Se validaron isótopos, pero no se encontró información extra en la BD.")

    # Limpieza
    try: os.remove(ruta_temp)
    except: pass

print("\n" + "="*70)
print("Proceso FINALIZADO.")


#################################################

nombre_input_Au = input("Ingrese el nombre del archivo .k0s del comparador de Au (Sin extensión): ").strip()
w_i = input("Ingrese la masa de la muestra (g): ").strip() # 0.26378
w_i_c_Au = input("Ingrese la masa del comparador (ug): ").strip() # 44.68
f_ini = pedir_fecha("inicio") #
h_ini = pedir_hora("inicio") #
f_fin = pedir_fecha("fin") #
h_fin = pedir_hora("fin") #
geometria = pedir_geometria()


# ==============================================================================
#                 CARGA DE BASE DE DATOS (k0s)
# ==============================================================================

print("\n" + "="*70)
print("PROCESANDO k0s (MUESTRAS)")

input_file = '/content/drive/MyDrive/k0/'+nombre_base+'.k0s'
output_file = '/content/drive/MyDrive/k0/'+nombre_base+'_k0s.xlsx'

LINES_TO_READ = 10 # Leer solo las 10 primeras líneas


# --- k0s archivo muestras ---
# --- EJECUCIÓN Y VISUALIZACIÓN ---
# 1. Ejecutar la función principal y capturar el DataFrame
df_metadata = extract_and_tokenize_metadata(input_file, output_file, LINES_TO_READ)

# 2. Si el DataFrame es válido, ejecutar la nueva función de extracción
if df_metadata is not None:
    #print("\n=======================================================")
    #print("VISUALIZACIÓN DEL DATAFRAME DE METADATOS (TABLA COMPLETA):")
    #print("=======================================================")
    #print(df_metadata.to_string(index=False, header=False)))'''

    # --- LLAMADA A LA NUEVA FUNCIÓN QUE EXTRAE DATOS---
    f_med, hora_med, t_v, t_r = extraer_variables_clave(df_metadata)

    if f_med is not None:
        #print("\n=======================================================")
        #print("VARIABLES EXTRAÍDAS:")
        #print("=======================================================")
        print(f"Fecha de inicio de medición: {f_med}")
        print(f"Hora de inicio de medición: {hora_med}")
        print(f"Tiempo vivo: {t_v}")
        print(f"Tiempo real: {t_r}")
else:
    print("\nEl DataFrame no se pudo generar o la función devolvió None debido a un error.")
t_v = float(t_v)
t_r = float(t_r)


print("\n" + "="*70)

