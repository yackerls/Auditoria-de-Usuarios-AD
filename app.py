import streamlit as st
import pandas as pd
import json

# Configuración: Layout "wide"
st.set_page_config(page_title="Auditoría AD Local", layout="wide")

# --- Encabezado ---
col1, col2 = st.columns([2, 1.5])
with col1:
    st.title("🛡️ Reporte de Seguridad AD")
    st.caption("Modo Privacidad: Procesamiento en memoria.")

with col2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        help="Sube el archivo JSON generado por PowerShell."
    )
st.divider()

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)

        # --- LIMPIEZA DE DATOS (FECHAS Y BLOQUEOS) ---
        
        # 1. Extraer la fecha del objeto de PowerShell
        def limpiar_fecha(val):
            if isinstance(val, dict) and 'DateTime' in val:
                return val['DateTime']
            return val

        df['Fecha_Raw'] = df['UltimaFechaCambio'].apply(limpiar_fecha)
        # Convertir a formato fecha real para poder ordenar
        df['Fecha_Objeto'] = pd.to_datetime(df['Fecha_Raw'], errors='coerce')
        # Crear columna de visualización limpia (YYYY-MM-DD)
        df['Ultimo Cambio'] = df['Fecha_Objeto'].dt.strftime('%d/%m/%Y')

        # 2. Asegurar que las métricas funcionen
        df_bloqueados = df[df['Estado'] == 'Bloqueado'].copy()
        df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()

        # --- MÉTRICAS ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Usuarios", len(df))
        m2.metric("Bloqueados", len(df_bloqueados), delta_color="inverse")
        m3.metric("Claves > 90 días", len(df_expirados), delta_color="inverse")

        st.markdown("---")

        # --- TABLA DE ACCIONES ---
        if 'filtro_ad' not in st.session_state:
            st.session_state.filtro_ad = None

        c_res = st.columns([3, 1, 1])
        c_res[0].markdown("**Categoría**")
        c_res[1].markdown("**Cantidad**")
        c_res[2].markdown("**Acción**")

        # Fila Bloqueados
        r1 = st.columns([3, 1, 1])
        r1[0].write("🚫 Usuarios Bloqueados")
        r1[1].write(len(df_bloqueados))
        if r1[2].button("🔍 Ver", key="btn_b"):
            st.session_state.filtro_ad = "Bloqueado"

        # Fila Expirados
        r2 = st.columns([3, 1, 1])
        r2[0].write("🔑 Claves > 90 días")
        r2[1].write(len(df_expirados))
        if r2[2].button("🔍 Ver", key="btn_e"):
            st.session_state.filtro_ad = "Expirado"

        st.divider()

        # --- LÓGICA FILTRO ---
        df_display = df
        titulo_tabla = "📋 Todos los Usuarios"

        if st.session_state.filtro_ad == "Bloqueado":
            df_display = df_bloqueados
            titulo_tabla = "🚨 Solo Usuarios Bloqueados"
        elif st.session_state.filtro_ad == "Expirado":
            df_display = df_expirados
            titulo_tabla = "⚠️ Solo Claves Expiradas (> 90 días)"

        if st.session_state.filtro_ad:
            if st.button("❌ Quitar Filtro"):
                st.session_state.filtro_ad = None
                st.rerun()

        st.subheader(titulo_tabla)
        
        # Mapeo de columnas finales
        cols_finales = {
            'DisplayName': 'Nombre',
            'EmailAddress': 'Correo',
            'Estado': 'Estado',
            'DiasDesdeCambioClave': 'Días Antigüedad',
            'Ultimo Cambio': 'Fecha Cambio'
        }

        # Mostrar tabla ordenada por los días de antigüedad (mayor a menor)
        df_final = df_display[list(cols_finales.keys())].rename(columns=cols_finales)
        df_final = df_final.sort_values(by='Días Antigüedad', ascending=False)

        st.dataframe(df_final, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Por favor, carga el archivo 'ad_audit.json'.")