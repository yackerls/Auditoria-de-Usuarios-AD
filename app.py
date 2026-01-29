import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Auditoría de Contraseñas AD", layout="wide", page_icon="🔑")

# --- Encabezado ---
col_t1, col_t2 = st.columns([2, 1.5])
with col_t1:
    st.title("🔑 Auditoría de Seguridad: Contraseñas AD")
    st.caption("Filtro de seguridad: Usuarios con más de 3 meses sin cambio de clave.")

with col_t2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        help="Sube el archivo generado por PowerShell."
    )

st.divider()

# --- PROCESAMIENTO ---
df = None

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)

        # Limpieza de Fechas
        def limpiar_fecha_ps(val):
            if isinstance(val, dict) and 'DateTime' in val:
                return val['DateTime']
            return val

        df['Fecha_Raw'] = df['UltimaFechaCambio'].apply(limpiar_fecha_ps)
        df['Fecha_Dt'] = pd.to_datetime(df['Fecha_Raw'], errors='coerce')
        df['Ultimo Cambio'] = df['Fecha_Dt'].dt.strftime('%d/%m/%Y')

        # Asegurar números
        df['DiasDesdeCambioClave'] = pd.to_numeric(df['DiasDesdeCambioClave'], errors='coerce').fillna(0).astype(int)
        
        # Dataframes de Alerta
        df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()
        df_activos = df[df['Estado'] == 'Activo'].copy()

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👈 Por favor, carga el archivo JSON para comenzar la auditoría.")

# --- INTERFAZ PRINCIPAL ---
if df is not None:
    # 1. Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Usuarios", len(df))
    m2.metric("Claves > 90 días", len(df_expirados), delta_color="inverse")
    m3.metric("Usuarios Activos", len(df_activos))

    st.markdown("### 📉 Resumen de Cumplimiento")
    
    if 'filtro_ad' not in st.session_state:
        st.session_state.filtro_ad = None

    # Tabla Resumen
    h_cols = st.columns([3, 1, 1])
    h_cols[0].markdown("**Categoría**")
    h_cols[1].markdown("**Cantidad**")
    h_cols[2].markdown("**Acción**")
    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    # Fila: Expirados
    r_cols = st.columns([3, 1, 1])
    r_cols[0].write("⚠️ Contraseñas Expiradas (> 3 meses)")
    r_cols[1].write(f"{len(df_expirados)} 👤")
    if r_cols[2].button("🔍 Ver Críticos", key="btn_exp"):
        st.session_state.filtro_ad = "Expirado"
        st.rerun()
    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    st.divider()

    # 2. Listado Detallado
    df_final = df
    mensaje_tabla = "Mostrando: Base de datos completa"

    if st.session_state.filtro_ad == "Expirado":
        df_final = df_expirados
        mensaje_tabla = "🚨 Filtro Activo: Usuarios con clave mayor a 90 días"

    col_sub, col_reset = st.columns([8, 2])
    col_sub.subheader("📋 Inventario de Usuarios")
    if st.session_state.filtro_ad:
        if col_reset.button("❌ Quitar Filtro"):
            st.session_state.filtro_ad = None
            st.rerun()

    st.info(mensaje_tabla)

    # Selección de columnas
    cols_map = {
        'DisplayName': 'Nombre',
        'EmailAddress': 'Correo',
        'Estado': 'Estado',
        'DiasDesdeCambioClave': 'Días Antigüedad',
        'Ultimo Cambio': 'Fecha Cambio'
    }

    df_view = df_final[list(cols_map.keys())].rename(columns=cols_map)
    df_view = df_view.sort_values(by='Días Antigüedad', ascending=False)

    # --- CORRECCIÓN DE COLOR (LEGIBILIDAD) ---
    def style_rows(row):
        # Si tiene más de 90 días, aplicamos un color de fondo melón suave y texto negro
        if row['Días Antigüedad'] > 90:
            return ['background-color: #ffcccc; color: black; font-weight: bold'] * len(row)
        return [''] * len(row)

    st.dataframe(
        df_view.style.apply(style_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # Botón Descarga
    csv = df_view.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte CSV",
        data=csv,
        file_name=f"auditoria_passwords_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )