import streamlit as st
import pandas as pd
import json

# Configuración: Layout "wide"
st.set_page_config(page_title="Auditoría AD Local", layout="wide")

# --- Encabezado y Carga de Archivos ---
col1, col2 = st.columns([2, 1.5])
with col1:
    st.title("🛡️ Reporte de Seguridad AD")
    st.caption("Modo Privacidad: Los datos se procesan en memoria y no se guardan.")

with col2:
    uploaded_file = st.file_uploader(
        "📂 Cargar reporte ad_audit.json",
        type=["json"],
        help="Sube el archivo JSON generado por PowerShell para analizarlo al instante."
    )
st.divider()

# --- LÓGICA DE CARGA ---
df = None
source_message = ""

if uploaded_file is not None:
    try:
        # Leer directamente desde la subida
        data = json.load(uploaded_file)
        df = pd.DataFrame(data)
        source_message = f"✅ Analizando reporte temporal: **{uploaded_file.name}**"
        
    except Exception as e:
        st.error(f"Error al procesar el archivo JSON: {e}")
else:
    st.info("👈 Sube el archivo JSON generado por tu script de AD para ver el reporte.")

# --- INICIO DE LA APP PRINCIPAL ---
if df is not None:
    st.success(source_message)
    try:
        # Verificar columnas necesarias
        columnas_req = ['Estado', 'DiasDesdeCambioClave', 'DisplayName']
        if all(col in df.columns for col in columnas_req):
            
            # --- PREPARAR DATOS ---
            df_bloqueados = df[df['Estado'] == 'Bloqueado'].copy()
            df_expirados = df[df['DiasDesdeCambioClave'] > 90].copy()

            # --- PARTE 1: TABLA RESUMEN COMPACTA ---
            st.markdown("### 📉 Resumen de Alertas Críticas")
            
            # Estado de la sesión para filtros
            if 'filtro_ad' not in st.session_state:
                st.session_state.filtro_ad = None

            # Crear métricas rápidas
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Usuarios", len(df))
            m2.metric("Bloqueados", len(df_bloqueados))
            m3.metric("Claves > 90 días", len(df_expirados))

            st.markdown("---")
            
            # Tabla de acciones estilo el proyecto anterior
            header_cols = st.columns([3, 1, 1])
            header_cols[0].markdown("**Categoría de Riesgo**")
            header_cols[1].markdown("**Cantidad**")
            header_cols[2].markdown("**Acción**")
            st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)

            # Fila 1: Bloqueados
            r1_cols = st.columns([3, 1, 1])
            r1_cols[0].write("🚫 Usuarios Bloqueados")
            r1_cols[1].write(f"{len(df_bloqueados)} 👤")
            if r1_cols[2].button("🔍 Ver Bloqueados", key="btn_bloq"):
                st.session_state.filtro_ad = "Bloqueado"
                st.rerun()

            st.markdown("<hr style='margin:0.5rem 0; border-top: 1px solid rgba(0, 0, 0, 0.1);'>", unsafe_allow_html=True)

            # Fila 2: Contraseñas viejas
            r2_cols = st.columns([3, 1, 1])
            r2_cols[0].write("🔑 Contraseñas > 3 meses (90 días)")
            r2_cols[1].write(f"{len(df_expirados)} 👤")
            if r2_cols[2].button("🔍 Ver Expirados", key="btn_exp"):
                st.session_state.filtro_ad = "Expirado"
                st.rerun()

            st.divider()

            # --- PARTE 2: LÓGICA DE FILTRADO ---
            df_filtrado = df
            mensaje_filtro = "Mostrando: Todos los usuarios del AD"

            if st.session_state.filtro_ad == "Bloqueado":
                df_filtrado = df_bloqueados
                mensaje_filtro = "🚨 Filtro Activo: Solo Usuarios Bloqueados"
            elif st.session_state.filtro_ad == "Expirado":
                df_filtrado = df_expirados
                mensaje_filtro = "⚠️ Filtro Activo: Usuarios con Clave > 90 días"

            if st.session_state.filtro_ad:
                if st.button("❌ Quitar Filtro"):
                    st.session_state.filtro_ad = None
                    st.rerun()

            # --- PARTE 3: INVENTARIO DETALLADO ---
            st.subheader("📋 Detalle de Usuarios")
            st.info(mensaje_filtro)

            # Mapeo de columnas para que se vean bien
            cols_map = {
                'DisplayName': 'Nombre Completo',
                'EmailAddress': 'Correo Electrónico',
                'Estado': 'Estado Cuenta',
                'DiasDesdeCambioClave': 'Días desde última clave',
                'UltimaFechaCambio': 'Fecha de Cambio'
            }

            cols_existentes = [c for c in cols_map.keys() if c in df_filtrado.columns]
            
            if cols_existentes:
                df_final = df_filtrado[cols_existentes].rename(columns=cols_map)
                
                # Estilo condicional: Rojo si está bloqueado o > 90 días
                def highlight_risks(row):
                    style = [''] * len(row)
                    if row['Estado Cuenta'] == 'Bloqueado' or row['Días desde última clave'] > 90:
                        style = ['background-color: #ffe6e6'] * len(row)
                    return style

                st.dataframe(
                    df_final.style.apply(highlight_risks, axis=1),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No se encontraron columnas de detalle en el JSON.")

        else:
            st.error("El JSON debe contener: 'Estado', 'DiasDesdeCambioClave' y 'DisplayName'.")

    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")