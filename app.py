import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Configuración: Layout "wide"
st.set_page_config(page_title="Auditoría de Contraseñas AD", layout="wide")

# --- Encabezado y Carga de Archivos ---
col1, col2 = st.columns([2, 1.5])
with col1:
    st.title("🔒 Reporte de Seguridad: Contraseñas")
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
    st.info("👈 Sube el archivo JSON en el panel de arriba para ver el reporte.")

# --- INICIO DE LA APP PRINCIPAL ---
if df is not None:
    st.success(source_message)
    
    # --- PREPARAR DATOS ---
    # Filtrar usuarios que exceden los 90 días (3 meses)
    df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()
    
    # --- PARTE 1: TABLA RESUMEN COMPACTA (Estilo Office) ---
    st.markdown("### 📉 Resumen de Cumplimiento")
    st.caption("Haz clic en 'Ver' para filtrar la lista de abajo.")
    
    # Estado de la sesión para filtros
    if 'licencia_seleccionada' not in st.session_state:
        st.session_state.licencia_seleccionada = None

    # Cabecera de tabla de resumen
    header_cols = st.columns([3, 1, 1])
    header_cols[0].markdown("**Estado de Política**")
    header_cols[1].markdown("**Usuarios**")
    header_cols[2].markdown("**Acción**")
    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    # Fila: Usuarios fuera de política
    r1_cols = st.columns([3, 1, 1])
    r1_cols[0].write("⚠️ Contraseñas Expiradas (> 90 días)")
    r1_cols[1].write(f"{len(df_expirados)} 👤")
    if r1_cols[2].button("🔍 Ver", key="btn_criticos"):
        st.session_state.licencia_seleccionada = "Expirado"
        st.rerun()

    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    # Fila: Usuarios al día
    df_al_dia = df[df['DiasDesdeCambioClave'] <= 90]
    r2_cols = st.columns([3, 1, 1])
    r2_cols[0].write("✅ Contraseñas al Día")
    r2_cols[1].write(f"{len(df_al_dia)} 👤")
    if r2_cols[2].button("🔍 Ver", key="btn_aldia"):
        st.session_state.licencia_seleccionada = "AlDia"
        st.rerun()

    st.divider()

    # --- PARTE 2: LÓGICA DE FILTRADO ---
    df_filtrado = df
    mensaje_filtro = "Mostrando: Todos los usuarios"

    if st.session_state.licencia_seleccionada == "Expirado":
        df_filtrado = df_expirados
        mensaje_filtro = "🚨 Filtro Activo: Usuarios fuera de política (> 90 días)"
    elif st.session_state.licencia_seleccionada == "AlDia":
        df_filtrado = df_al_dia
        mensaje_filtro = "✅ Filtro Activo: Usuarios cumpliendo la política"

    if st.session_state.licencia_seleccionada:
        if st.button("❌ Quitar Filtro"):
            st.session_state.licencia_seleccionada = None
            st.rerun()

    # --- PARTE 3: INVENTARIO DETALLADO ---
    col_header, col_count = st.columns([8, 2])
    col_header.subheader("📋 Inventario Detallado")
    col_count.metric("Encontrados", len(df_filtrado))
    
    st.info(mensaje_filtro)

    # Mapeo de columnas para que coincida con lo que necesitas
    cols_map = {
        'DisplayName': 'Nombre',
        'EmailAddress': 'Correo',
        'Estado': 'Estado Cuenta',
        'DiasDesdeCambioClave': 'Días de Antigüedad',
        'Fecha_Formateada': 'Último Cambio'
    }

    cols_existentes = [c for c in cols_map.keys() if c in df_filtrado.columns]
    
    if cols_existentes:
        df_final = df_filtrado[cols_existentes].rename(columns=cols_map)
        
        # Mostramos la tabla limpia sin colores raros que bloqueen la vista
        st.dataframe(
            df_final.sort_values(by='Días de Antigüedad', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        
        # Botón de descarga al final
        csv = df_final.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", data=csv, file_name="auditoria_ad.csv", mime='text/csv')
    else:
        st.warning("No se encontraron las columnas necesarias en el archivo.")