import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import io

# ================= CONFIGURACIÓN Y ESTILO VISUAL =================
st.set_page_config(page_title="Metales Flix Pro", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; text-align: left; padding-left: 10px; }
    [data-testid="stSidebar"] .stButton>button {
        background-color: #1e2129;
        color: white;
        border: 1px solid #3d414b;
        margin-bottom: 5px;
        height: 45px;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        border-color: #006400;
        color: #00fb00;
    }
    h1, h2, h3 { color: #006400 !important; font-family: 'Segoe UI'; font-weight: bold; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "metales_flix.xlsx"

# --- Funciones de Datos ---
def cargar_ho_ja(sheet):
    try: return pd.read_excel(DB_FILE, sheet_name=sheet)
    except: return pd.DataFrame()

def guardar_hoja(df, sheet):
    with pd.ExcelWriter(DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)
    return True

# --- Control de Estado ---
if "menu_sel" not in st.session_state: st.session_state.menu_sel = "Logística"
if "selector_id" not in st.session_state: st.session_state.selector_id = 0
if "temp_nom" not in st.session_state: st.session_state.temp_nom = ""
if "temp_doc" not in st.session_state: st.session_state.temp_doc = ""
if "m_id" not in st.session_state: st.session_state.m_id = ""
if "m_nom" not in st.session_state: st.session_state.m_nom = ""

def limpiar_todo():
    st.session_state.temp_nom = ""
    st.session_state.temp_doc = ""
    st.session_state.m_id = ""
    st.session_state.m_nom = ""
    st.session_state.selector_id += 1
    st.rerun()

# ================= MENÚ LATERAL =================
with st.sidebar:
    st.title("🛰️ METALES FLIX")
    if st.button("🏠 Logística Principal"):
        st.session_state.menu_sel = "Logística"
        st.rerun()
    if st.button("👮 Maestro de Guardas"):
        st.session_state.menu_sel = "Guardas"
        st.rerun()
    if st.button("🚛 Maestro de Transportistas"):
        st.session_state.menu_sel = "Transportistas"
        st.rerun()
    if st.button("📊 Reportes y Excel"):
        st.session_state.menu_sel = "Reportes"
        st.rerun()

# ================= LÓGICA DE PÁGINAS =================

if st.session_state.menu_sel == "Logística":
    st.header("🛸 Control de Arribos y Salidas")
    df_reg = cargar_ho_ja('Registros')
    df_transp = cargar_ho_ja('Transportistas')
    df_guardas = cargar_ho_ja('Guardas')

    # Validación anti-error para Logística
    if "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
        idx = st.session_state.tabla_p.selection.rows[0]
        if idx < len(df_reg):
            st.session_state.temp_nom = str(df_reg.iloc[idx]["Nombre"])
            st.session_state.temp_doc = str(df_reg.iloc[idx]["Documento"])

    with st.expander("➕ FORMULARIO DE REGISTRO / EDICIÓN", expanded=True):
        opciones = ["Digitación Manual"]
        if not df_transp.empty:
            opciones += (df_transp['Nombre'].astype(str) + " (" + df_transp['ID_Transportista'].astype(str) + ")").tolist()
        
        def al_seleccionar_maestro():
            sel = st.session_state[f"bus_master_{st.session_state.selector_id}"]
            if sel != "Digitación Manual":
                doc_id = sel.split('(')[-1].replace(')', '')
                match = df_transp[df_transp['ID_Transportista'].astype(str) == doc_id].iloc[0]
                st.session_state.temp_nom = str(match['Nombre'])
                st.session_state.temp_doc = str(match['ID_Transportista'])
                st.session_state.selector_id += 1 

        st.selectbox("BUSCAR EN MAESTRO:", opciones, key=f"bus_master_{st.session_state.selector_id}", on_change=al_seleccionar_maestro)
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE COMPLETO:", value=st.session_state.temp_nom, key=f"nom_in_{st.session_state.selector_id}")
            documento = st.text_input("DOCUMENTO DE IDENTIDAD:", value=st.session_state.temp_doc, key=f"doc_in_{st.session_state.selector_id}")
            placa = st.text_input("NÚMERO DE PLACA:", key=f"p_{st.session_state.selector_id}")
            cliente = st.text_input("CLIENTE / DESTINO:", key=f"c_{st.session_state.selector_id}")
            factura = st.text_area("NÚMEROS DE FACTURA:", key=f"f_{st.session_state.selector_id}")
        with col2:
            c_f, c_h = st.columns(2)
            f_ar, h_ar = c_f.date_input("FECHA ARRIBO"), c_h.time_input("HORA ARRIBO")
            f_en, h_en = c_f.date_input("FECHA ENTRADA"), c_h.time_input("HORA ENTRADA", time(0,0))
            f_sa, h_sa = c_f.date_input("FECHA SALIDA"), c_h.time_input("HORA SALIDA", time(0,0))
            list_guardas = df_guardas['Nombre'].tolist() if not df_guardas.empty else ["No hay guardas"]
            guarda_sel = st.selectbox("GUARDA EN TURNO:", list_guardas)
            obs = st.text_area("OBSERVACIONES:", key=f"o_{st.session_state.selector_id}")

        b1, b2, b3 = st.columns([2,1,1])
        if b1.button("🚀 GUARDAR / ACTUALIZAR", type="primary"):
            dt_ar, dt_en, dt_sa = f"{f_ar.strftime('%d/%m/%Y')} {h_ar.strftime('%H:%M')}", f"{f_en.strftime('%d/%m/%Y')} {h_en.strftime('%H:%M')}", f"{f_sa.strftime('%d/%m/%Y')} {h_sa.strftime('%H:%M')}"
            if not df_reg.empty and str(documento) in df_reg['Documento'].astype(str).values:
                df_reg.loc[df_reg['Documento'].astype(str) == str(documento), ["Nombre", "Placa", "Cliente", "Arribo", "Entrada", "Salida", "Factura", "Guarda", "Observaciones"]] = [nombre, placa, cliente, dt_ar, dt_en, dt_sa, factura, guarda_sel, obs]
                df_final = df_reg
            else:
                nuevo_id = df_reg['ID'].max() + 1 if not df_reg.empty else 1
                df_final = pd.concat([df_reg, pd.DataFrame([[nuevo_id, nombre, documento, placa, cliente, dt_ar, dt_en, dt_sa, factura, guarda_sel, obs]], columns=df_reg.columns)], ignore_index=True)
            guardar_hoja(df_final, 'Registros')
            st.success("✅ Guardado")
            limpiar_todo()
        if b2.button("🗑️ ELIMINAR") and "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
            guardar_hoja(df_reg.drop(df_reg.index[st.session_state.tabla_p.selection.rows[0]]), 'Registros')
            limpiar_todo()
        if b3.button("🧹 LIMPIAR"): limpiar_todo()
    st.dataframe(df_reg, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_p")

elif st.session_state.menu_sel == "Guardas":
    st.header("👮 Maestro de Guardas")
    df_g = cargar_ho_ja('Guardas')
    # ARREGLO DEL ERROR: Validar índice antes de acceder
    if "tabla_g" in st.session_state and st.session_state.tabla_g.selection.rows:
        idx = st.session_state.tabla_g.selection.rows[0]
        if idx < len(df_g):
            st.session_state.m_id = str(df_g.iloc[idx]["Empleado_ID"])
            st.session_state.m_nom = str(df_g.iloc[idx]["Nombre"])

    with st.expander("📝 GESTIÓN DE PERSONAL", expanded=True):
        id_g = st.text_input("Cédula / ID:", value=st.session_state.m_id, key=f"gi_{st.session_state.selector_id}")
        nom_g = st.text_input("Nombre Completo:", value=st.session_state.m_nom, key=f"gn_{st.session_state.selector_id}")
        c1, c2, c3 = st.columns(3)
        if c1.button("💾 GUARDAR/EDITAR", type="primary"):
            if not df_g.empty and str(id_g) in df_g['Empleado_ID'].astype(str).values:
                df_g.loc[df_g['Empleado_ID'].astype(str) == str(id_g), "Nombre"] = nom_g
            else:
                df_g = pd.concat([df_g, pd.DataFrame([[id_g, nom_g]], columns=df_g.columns)], ignore_index=True)
            guardar_hoja(df_g, 'Guardas'); limpiar_todo()
        if c2.button("🗑️ BORRAR SELECCIÓN") and "tabla_g" in st.session_state and st.session_state.tabla_g.selection.rows:
            guardar_hoja(df_g.drop(df_g.index[st.session_state.tabla_g.selection.rows[0]]), 'Guardas'); limpiar_todo()
        if c3.button("🧹 NUEVO"): limpiar_todo()
    st.dataframe(df_g, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_g")

elif st.session_state.menu_sel == "Transportistas":
    st.header("🚛 Maestro de Transportistas")
    df_t = cargar_ho_ja('Transportistas')
    # ARREGLO DEL ERROR: Validar índice antes de acceder
    if "tabla_t" in st.session_state and st.session_state.tabla_t.selection.rows:
        idx = st.session_state.tabla_t.selection.rows[0]
        if idx < len(df_t):
            st.session_state.m_id = str(df_t.iloc[idx]["ID_Transportista"])
            st.session_state.m_nom = str(df_t.iloc[idx]["Nombre"])

    with st.expander("📝 GESTIÓN DE TRANSPORTISTAS", expanded=True):
        id_t = st.text_input("Cédula / ID:", value=st.session_state.m_id, key=f"ti_{st.session_state.selector_id}")
        nom_t = st.text_input("Nombre Completo:", value=st.session_state.m_nom, key=f"tn_{st.session_state.selector_id}")
        c1, c2, c3 = st.columns(3)
        if c1.button("💾 GUARDAR/EDITAR", type="primary"):
            if not df_t.empty and str(id_t) in df_t['ID_Transportista'].astype(str).values:
                df_t.loc[df_t['ID_Transportista'].astype(str) == str(id_t), "Nombre"] = nom_t
            else:
                df_t = pd.concat([df_t, pd.DataFrame([[id_t, nom_t, "FISICA"]], columns=df_t.columns)], ignore_index=True)
            guardar_hoja(df_t, 'Transportistas'); limpiar_todo()
        if c2.button("🗑️ BORRAR SELECCIÓN") and "tabla_t" in st.session_state and st.session_state.tabla_t.selection.rows:
            guardar_hoja(df_t.drop(df_t.index[st.session_state.tabla_t.selection.rows[0]]), 'Transportistas'); limpiar_todo()
        if c3.button("🧹 NUEVO"): limpiar_todo()
    st.dataframe(df_t, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_t")

elif st.session_state.menu_sel == "Reportes":
    st.header("📊 Reportes")
    df_rep = cargar_ho_ja('Registros')
    if not df_rep.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, sheet_name='Registros', index=False)
        st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="MetalesFlix_Logistica.xlsx", type="primary")
        st.dataframe(df_rep, use_container_width=True)