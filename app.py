import streamlit as st
import pandas as pd
import json
from datetime import datetime

# 1. Configuración de la página (Layout ancho para máxima visibilidad)
st.set_page_config(page_title="Auditoría AD Local", layout="wide", page_icon="🛡️")

# --- Encabezado y Carga de Archivos ---
col_t1, col_t2 = st.columns([2, 1.5])
with col_t1:
    st.title("🛡️ Auditoría de Identidad - AD Local")
    st.caption("Modo Privacidad: Procesamiento local en memoria. Los datos no se almacenan en el servidor.")

with col_t2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        help="Sube el archivo generado por el script de PowerShell para analizarlo."
    )

st.divider()

# --- LÓGICA DE PROCESAMIENTO (SOLO EN MEMORIA) ---
df = None

if uploaded_file is not None:
    try:
        # Cargar JSON
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)

        # A. Limpieza de Fechas (Extracción del objeto de PowerShell)
        def limpiar_fecha_ps(val):
            if isinstance(val, dict) and 'DateTime' in val:
                return val['DateTime']
            return val

        df['Fecha_Raw'] = df['UltimaFechaCambio'].apply(limpiar_fecha_ps)
        df['Fecha_Dt'] = pd.to_datetime(df['Fecha_Raw'], errors='coerce')
        # Formato legible para el usuario
        df['Ultimo Cambio'] = df['Fecha_Dt'].dt.strftime('%d/%m/%Y %H:%M')

        # B. Asegurar tipos de datos
        df['DiasDesdeCambioClave'] = pd.to_numeric(df['DiasDesdeCambioClave'], errors='coerce').fillna(0).astype(int)
        
        # C. Definir Dataframes de Alerta
        df_bloqueados = df[df['Estado'] == 'Bloqueado'].copy()
        df_deshabilitados = df[df['Estado'] == 'Deshabilitado'].copy()
        df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("👈 Por favor, carga el archivo JSON generado por tu script de AD para comenzar.")

# --- INTERFAZ PRINCIPAL ---
if df is not None:
    st.success(f"✅ Archivo analizado correctamente: **{uploaded_file.name}**")

    # 1. Métricas Superiores
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Usuarios", len(df))
    m2.metric("Bloqueados", len(df_bloqueados), delta_color="inverse")
    m3.metric("Claves > 90 días", len(df_expirados), delta_color="inverse")
    m4.metric("Deshabilitados", len(df_deshabilitados))

    st.markdown("### 📉 Resumen de Riesgos")
    st.caption("Haz clic en 'Ver' para filtrar el listado detallado.")

    # 2. Tabla Resumen Estilo "Proyecto O365"
    if 'filtro_ad' not in st.session_state:
        st.session_state.filtro_ad = None

    # Cabecera de la tabla personalizada
    h_cols = st.columns([3, 1, 1])
    h_cols[0].markdown("**Categoría de Auditoría**")
    h_cols[1].markdown("**Cantidad**")
    h_cols[2].markdown("**Acción**")
    st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    # Filas de la tabla resumen
    categorias = [
        {"nombre": "🚫 Usuarios Bloqueados (Lockout)", "count": len(df_bloqueados), "key": "Bloqueado"},
        {"nombre": "⚠️ Contraseñas Expiradas (> 3 meses)", "count": len(df_expirados), "key": "Expirado"},
        {"nombre": "🌑 Cuentas Deshabilitadas", "count": len(df_deshabilitados), "key": "Deshabilitado"}
    ]

    for i, cat in enumerate(categorias):
        r_cols = st.columns([3, 1, 1])
        r_cols[0].write(cat["nombre"])
        r_cols[1].write(f"{cat['count']} 👤")
        if r_cols[2].button("🔍 Ver", key=f"btn_{i}"):
            st.session_state.filtro_ad = cat["key"]
            st.rerun()
        st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0,0,0,0.1);'>", unsafe_allow_html=True)

    st.divider()

    # 3. Listado Detallado con Filtros
    df_final = df
    mensaje_tabla = "Mostrando: Todos los usuarios"

    if st.session_state.filtro_ad == "Bloqueado":
        df_final = df_bloqueados
        mensaje_tabla = "Filtro: Usuarios Bloqueados actualmente"
    elif st.session_state.filtro_ad == "Expirado":
        df_final = df_expirados
        mensaje_tabla = "Filtro: Usuarios con contraseña mayor a 90 días"
    elif st.session_state.filtro_ad == "Deshabilitado":
        df_final = df_deshabilitados
        mensaje_tabla = "Filtro: Usuarios Deshabilitados"

    col_sub, col_reset = st.columns([8, 2])
    col_sub.subheader("📋 Inventario Detallado")
    if st.session_state.filtro_ad:
        if col_reset.button("❌ Quitar Filtro"):
            st.session_state.filtro_ad = None
            st.rerun()

    st.info(mensaje_tabla)

    # Selección de columnas para mostrar
    cols_map = {
        'DisplayName': 'Nombre',
        'EmailAddress': 'Correo',
        'Estado': 'Estado Cuenta',
        'DiasDesdeCambioClave': 'Días de Clave',
        'Ultimo Cambio': 'Última Fecha Cambio'
    }

    # Filtrar solo columnas existentes y renombrar
    df_view = df_final[list(cols_map.keys())].rename(columns=cols_map)
    
    # Ordenar por antigüedad de clave por defecto
    df_view = df_view.sort_values(by='Días de Clave', ascending=False)

    # Estilo condicional: Resaltar en rojo filas de riesgo
    def highlight_risks(row):
        style = [''] * len(row)
        if row['Estado Cuenta'] != 'Activo' or row['Días de Clave'] > 90:
            style = ['background-color: #ffeded'] * len(row)
        return style

    st.dataframe(
        df_view.style.apply(highlight_risks, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # Botón de Descarga
    csv = df_view.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Reporte en CSV",
        data=csv,
        file_name=f"auditoria_ad_{datetime.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )