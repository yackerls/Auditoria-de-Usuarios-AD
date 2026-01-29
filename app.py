import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Auditoría de Contraseñas", layout="wide", page_icon="🔑")

# --- Estilo CSS para mejorar la estética de las "Tarjetas" ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        border: 1px solid #e1e4e8;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- Encabezado ---
col_t1, col_t2 = st.columns([2, 1.2])
with col_t1:
    st.title("🛡️ Seguridad de Cuentas AD")
    st.caption("Control de cumplimiento de políticas de cambio de contraseña.")

with col_t2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        label_visibility="collapsed"
    )

st.divider()

# --- PROCESAMIENTO ---
if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)

        # Limpieza de Fechas (Extracción del objeto PowerShell)
        def limpiar_fecha_ps(val):
            if isinstance(val, dict) and 'DateTime' in val:
                return val['DateTime']
            return val

        df['Fecha_Raw'] = df['UltimaFechaCambio'].apply(limpiar_fecha_ps)
        df['Fecha_Dt'] = pd.to_datetime(df['Fecha_Raw'], errors='coerce')
        df['Ultimo Cambio'] = df['Fecha_Dt'].dt.strftime('%d/%m/%Y')

        # Cálculos
        df['DiasDesdeCambioClave'] = pd.to_numeric(df['DiasDesdeCambioClave'], errors='coerce').fillna(0).astype(int)
        df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()
        
        # 2. SECCIÓN DE TARJETAS (Métricas estilo Office)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Usuarios Analizados", len(df))
        with m2:
            st.metric("Fuera de Política (>90d)", len(df_expirados), delta=f"{len(df_expirados)} críticos", delta_color="inverse")
        with m3:
            cumplimiento = int(((len(df) - len(df_expirados)) / len(df)) * 100) if len(df) > 0 else 0
            st.metric("Índice de Cumplimiento", f"{cumplimiento}%")

        st.markdown("### 📋 Detalle de Auditoría")
        
        # Botones de Filtro rápido en una fila
        f1, f2, f3 = st.columns([1, 1, 4])
        if 'filtro' not in st.session_state: st.session_state.filtro = "Todos"
        
        if f1.button("Ver Todos", use_container_width=True): st.session_state.filtro = "Todos"
        if f2.button("Ver Críticos", use_container_width=True): st.session_state.filtro = "Críticos"

        # Aplicar Filtro
        df_final = df_expirados if st.session_state.filtro == "Críticos" else df

        # Selección de columnas y renombrado
        cols_map = {
            'DisplayName': 'Nombre',
            'EmailAddress': 'Correo',
            'Estado': 'Estado',
            'DiasDesdeCambioClave': 'Días Antigüedad',
            'Ultimo Cambio': 'Fecha Cambio'
        }
        
        df_view = df_final[list(cols_map.keys())].rename(columns=cols_map)
        df_view = df_view.sort_values(by='Días Antigüedad', ascending=False)

        # --- ESTILO DE TABLA PROFESIONAL ---
        def style_rows(row):
            # Usamos un color de fondo muy suave para no "tapar" el texto
            if row['Días Antigüedad'] > 90:
                return ['background-color: #fff4f4; color: #922b21; font-weight: bold'] * len(row)
            return [''] * len(row)

        st.dataframe(
            df_view.style.apply(style_rows, axis=1),
            use_container_width=True,
            hide_index=True
        )

        # Botón de descarga al pie
        csv = df_view.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte CSV", data=csv, file_name="auditoria_ad.csv", mime='text/csv')

    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
else:
    st.info("👋 Sube el archivo JSON para generar el reporte de cumplimiento.")