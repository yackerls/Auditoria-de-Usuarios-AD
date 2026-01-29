import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Auditoría AD Local", layout="wide")

st.title("🛡️ Auditoría de Identidad - Active Directory")

# --- SECCIÓN DE CARGA DE DATOS ---
st.sidebar.header("Configuración")
uploaded_file = st.sidebar.file_uploader("Subir reporte ad_audit.json", type=['json'])

if uploaded_file is not None:
    # Leer el archivo subido
    data = json.load(uploaded_file)
    df = pd.DataFrame(data)
    
    # --- PROCESAMIENTO ---
    # Convertir fechas para cálculos si es necesario
    df['UltimaFechaCambio'] = pd.to_datetime(df['UltimaFechaCambio'])
    
    # Métricas
    bloqueados = df[df['Estado'] == 'Bloqueado']
    fuera_politica = df[df['DiasDesdeCambioClave'] > 90]

    # Indicadores visuales
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Usuarios", len(df))
    c2.metric("Cuentas Bloqueadas", len(bloqueados))
    c3.metric("Claves > 90 días", len(fuera_politica))

    # --- TABLAS DETALLADAS ---
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["⚠️ Alertas Críticas", "🚫 Usuarios Bloqueados", "👥 Todos los Usuarios"])

    with tab1:
        st.subheader("Contraseñas que exceden los 3 meses")
        if not fuera_politica.empty:
            st.warning(f"Se encontraron {len(fuera_politica)} usuarios que deben cambiar su clave.")
            st.table(fuera_politica[['DisplayName', 'EmailAddress', 'DiasDesdeCambioClave', 'UltimaFechaCambio']])
        else:
            st.success("¡Cumplimiento del 100%! Todas las claves están al día.")

    with tab2:
        st.subheader("Usuarios con cuenta bloqueada")
        if not bloqueados.empty:
            st.error(f"Hay {len(bloqueados)} usuarios bloqueados actualmente.")
            st.dataframe(bloqueados[['DisplayName', 'EmailAddress', 'Estado']], use_container_width=True)
        else:
            st.info("No hay usuarios bloqueados en este momento.")

    with tab3:
        st.subheader("Base de datos completa")
        st.dataframe(df, use_container_width=True)

else:
    st.info("Esperando archivo JSON... Por favor, sube el reporte generado por PowerShell en la barra lateral.")