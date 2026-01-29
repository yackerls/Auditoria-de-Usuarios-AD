import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Configuración: Layout "wide"
st.set_page_config(page_title="Auditoría de Cuentas AD", layout="wide")

# --- Encabezado y Carga de Archivos ---
col1, col2 = st.columns([2, 1.5])
with col1:
    st.title("🔒 Reporte de Seguridad: Identidades AD")
    st.caption("Modo Privacidad: Los datos se procesan en memoria y no se guardan.")

with col2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        help="Sube el archivo JSON generado por PowerShell."
    )
st.divider()

# --- LÓGICA DE CARGA ---
df = None
source_message = ""

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        
        # Limpieza de Fechas de PowerShell
        def limpiar_fecha_ps(val):
            if isinstance(val, dict) and 'DateTime' in val:
                return val['DateTime']
            return val

        df['Fecha_Raw'] = df['UltimaFechaCambio'].apply(limpiar_fecha_ps)
        df['Fecha_Dt'] = pd.to_datetime(df['Fecha_Raw'], errors='coerce')
        df['Fecha_Formateada'] = df['Fecha_Dt'].dt.strftime('%d/%m/%Y')
        
        source_message = f"✅ Analizando reporte: **{uploaded_file.name}**"
        
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👈 Sube el archivo JSON para ver el análisis de cuentas.")

# --- INICIO DE LA APP PRINCIPAL ---
if df is not None:
    st.success(source_message)
    
    # --- PREPARAR DATOS ---
    df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()
    df_deshabilitados = df[df['Estado'] == 'Deshabilitado'].copy()
    df_al_dia = df[(df['DiasDesdeCambioClave'] <= 90) & (df['Estado'] == 'Activo')].copy()
    
    # --- PARTE 1: TABLA RESUMEN COMPACTA (Estilo Office) ---
    st.markdown("### 📉 Resumen de Cumplimiento")
    st.caption("Haz clic en 'Ver' para filtrar la lista detallada.")
    
    if 'filtro_seleccionado' not in st.session_state:
        st.session_state.filtro_seleccionado = None

    header_cols = st.columns([3, 1, 1])
    header_cols[0].markdown("**Estado de la Cuenta / Política**")
    header_cols[1].markdown("**Usuarios**")
    header_cols[2].markdown("**Acción**")
    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)

    # Fila 1: Expirados
    r1_cols = st.columns([3, 1, 1])
    r1_cols[0].write("⚠️ Contraseñas Expiradas (> 90 días)")
    r1_cols[1].write(f"{len(df_expirados)} 👤")
    if r1_cols[2].button("🔍 Ver", key="btn_expirados"):
        st.session_state.filtro_seleccionado = "Expirado"
        st.rerun()

    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)

    # Fila 2: Deshabilitados
    r2_cols = st.columns([3, 1, 1])
    r2_cols[0].write("🌑 Cuentas Deshabilitadas")
    r2_cols[1].write(f"{len(df_deshabilitados)} 👤")
    if r2_cols[2].button("🔍 Ver", key="btn_deshab"):
        st.session_state.filtro_seleccionado = "Deshabilitado"
        st.rerun()

    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)

    # Fila 3: Usuarios al día
    r3_cols = st.columns([3, 1, 1])
    r3_cols[0].write("✅ Contraseñas al Día (Activos)")
    r3_cols[1].write(f"{len(df_al_dia)} 👤")
    if r3_cols[2].button("🔍 Ver", key="btn_aldia"):
        st.session_state.filtro_seleccionado = "AlDia"
        st.rerun()

    st.divider()

    # --- PARTE 2: BUSCADOR Y LÓGICA DE FILTRADO ---
    st.subheader("📋 Inventario Detallado")
    
    # Buscador de usuarios
    search_query = st.text_input("🔍 Buscar por Nombre o Correo:", placeholder="Ej: Juan Perez o admin@dominio.com")

    df_filtrado = df
    mensaje_filtro = "Mostrando: Todos los usuarios"

    # Aplicar Filtro de Botones
    if st.session_state.filtro_seleccionado == "Expirado":
        df_filtrado = df_expirados
        mensaje_filtro = "🚨 Filtro Activo: Usuarios con clave > 90 días"
    elif st.session_state.filtro_seleccionado == "Deshabilitado":
        df_filtrado = df_deshabilitados
        mensaje_filtro = "🌑 Filtro Activo: Cuentas Deshabilitadas"
    elif st.session_state.filtro_seleccionado == "AlDia":
        df_filtrado = df_al_dia
        mensaje_filtro = "✅ Filtro Activo: Usuarios con clave reciente y activos"

    # Aplicar Filtro de Búsqueda (Texto)
    if search_query:
        df_filtrado = df_filtrado[
            df_filtrado['DisplayName'].str.contains(search_query, case=False, na=False) |
            df_filtrado['EmailAddress'].str.contains(search_query, case=False, na=False)
        ]
        mensaje_filtro += f" | 🔍 Búsqueda: '{search_query}'"

    # Botón para limpiar filtros
    col_msg, col_reset = st.columns([8, 2])
    col_msg.info(mensaje_filtro)
    if st.session_state.filtro_seleccionado or search_query:
        if col_reset.button("❌ Limpiar Todo"):
            st.session_state.filtro_seleccionado = None
            st.rerun()

    # --- PARTE 3: MESA DE DATOS ---
    cols_map = {
        'DisplayName': 'Nombre',
        'EmailAddress': 'Correo',
        'Estado': 'Estado Cuenta',
        'DiasDesdeCambioClave': 'Días Antigüedad',
        'Fecha_Formateada': 'Último Cambio'
    }

    cols_existentes = [c for c in cols_map.keys() if c in df_filtrado.columns]
    
    if cols_existentes:
        df_final = df_filtrado[cols_existentes].rename(columns=cols_map)
        
        st.metric("Usuarios en vista", len(df_final))
        
        st.dataframe(
            df_final.sort_values(by='Días Antigüedad', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Botón de descarga
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Vista Actual (CSV)", data=csv, file_name="auditoria_ad_filtrada.csv", mime='text/csv')
    else:
        st.warning("No se encontraron columnas para mostrar.")