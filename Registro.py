import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import io
import time as time_lib

# ================= CONFIGURACIÓN Y ESTILO VISUAL =================
st.set_page_config(page_title="Metales Flix Pro", layout="wide", page_icon="🛰️")

t_inicio = time_lib.time()

st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#0d0f12, #1e2129);
        color: white;
    }
    /* TÍTULO PERSONALIZADO */
    .titulo-flix {
        color: #a2d149 !important; 
        font-family: 'Segoe UI', sans-serif; 
        font-weight: 800;
        text-align: center;
        font-size: 2.2rem;
        margin-bottom: 20px;
        text-transform: uppercase;
    }
    h2, h3 { color: #a2d149 !important; }
    
    [data-testid="stSidebar"] .stButton>button {
        background-color: #16191f;
        color: #ffffff;
        border: 1px solid #a2d149;
        margin-bottom: 8px;
        height: 50px;
        width: 100%;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #a2d149;
        color: #000000;
        border-color: #ffffff;
    }
    
    .status-top {
        position: fixed; top: 0; left: 0; width: 100%; height: 25px;
        background-color: #0d0f12; color: #a2d149;
        font-family: monospace; font-size: 14px;
        display: flex; align-items: center; padding-left: 20px;
        z-index: 999999; border-bottom: 1px solid #a2d149;
    }
    </style>
    """, unsafe_allow_html=True)

latencia = round((time_lib.time() - t_inicio) * 1000, 2)
st.markdown(f'<div class="status-top">● SISTEMA FLIX: ONLINE | LATENCIA: {latencia}ms</div>', unsafe_allow_html=True)

DB_FILE = "metales_flix.xlsx"

# ================= FUNCIONES DE DATOS =================
@st.cache_data(ttl=1)
def cargar_hoja(sheet):
    try: 
        return pd.read_excel(DB_FILE, sheet_name=sheet)
    except: 
        if sheet == 'Registros':
            return pd.DataFrame(columns=["ID", "Nombre", "Documento", "Placa", "Cliente", "Arribo", "Entrada", "Salida", "Factura", "Guarda", "Observaciones"])
        elif sheet == 'Guardas':
            return pd.DataFrame(columns=["Empleado_ID", "Nombre"])
        elif sheet == 'Transportistas':
            return pd.DataFrame(columns=["ID_Transportista", "Nombre", "Tipo"])
        return pd.DataFrame()

def guardar_hoja(df, sheet):
    if not os.path.exists(DB_FILE):
        with pd.ExcelWriter(DB_FILE, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
    else:
        with pd.ExcelWriter(DB_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
    st.cache_data.clear()
    return True

# ================= CONTROL DE ESTADO =================
if "menu_sel" not in st.session_state: st.session_state.menu_sel = "Logística"
if "selector_id" not in st.session_state: st.session_state.selector_id = 0
if "temp_datos" not in st.session_state:
    st.session_state.temp_datos = {"Nombre": "", "Documento": "", "Placa": "", "Cliente": "", "Factura": "", "Obs": ""}
if "m_id" not in st.session_state: st.session_state.m_id = ""
if "m_nom" not in st.session_state: st.session_state.m_nom = ""

def limpiar_todo():
    st.session_state.temp_datos = {k: "" for k in st.session_state.temp_datos}
    st.session_state.m_id, st.session_state.m_nom = "", ""
    st.session_state.selector_id += 1
    st.rerun()

# ================= MENÚ LATERAL =================
with st.sidebar:
    st.markdown('<div class="titulo-flix">METALES FLIX</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 LOGÍSTICA PRINCIPAL"): 
        st.session_state.menu_sel = "Logística"
        limpiar_todo()
    if st.button("👮 MAESTRO DE GUARDAS"): 
        st.session_state.menu_sel = "Guardas"
        limpiar_todo()
    if st.button("🚛 TRANSPORTISTAS"): 
        st.session_state.menu_sel = "Transportistas"
        limpiar_todo()
    if st.button("📊 REPORTES Y EXCEL"): 
        st.session_state.menu_sel = "Reportes"
        st.rerun()

# ================= PÁGINA 1: LOGÍSTICA =================
if st.session_state.menu_sel == "Logística":
    df_reg = cargar_hoja('Registros')
    df_transp = cargar_hoja('Transportistas')
    df_guardas = cargar_hoja('Guardas')

    st.header("🛸 Registro de Movimientos")

    # LÓGICA DE SELECCIÓN DE FILA (RETORNO A CAMPOS)
    if "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
        idx_f = st.session_state.tabla_p.selection.rows[0]
        fila_sel = st.session_state.df_actual_p.iloc[idx_f]
        st.session_state.temp_datos = {
            "Nombre": str(fila_sel["Nombre"]),
            "Documento": str(fila_sel["Documento"]),
            "Placa": str(fila_sel["Placa"]),
            "Cliente": str(fila_sel["Cliente"]),
            "Factura": str(fila_sel["Factura"]),
            "Obs": str(fila_sel["Observaciones"])
        }

    with st.expander("➕ FORMULARIO DE ENTRADA / SALIDA", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE COMPLETO:", value=st.session_state.temp_datos["Nombre"], key=f"n_{st.session_state.selector_id}")
            documento = st.text_input("DOCUMENTO / NIT:", value=st.session_state.temp_datos["Documento"], key=f"d_{st.session_state.selector_id}")
            placa = st.text_input("PLACA VEHÍCULO:", value=st.session_state.temp_datos["Placa"], key=f"p_{st.session_state.selector_id}")
            cliente = st.text_input("CLIENTE / DESTINO:", value=st.session_state.temp_datos["Cliente"], key=f"c_{st.session_state.selector_id}")
            factura = st.text_area("FACTURAS:", value=st.session_state.temp_datos["Factura"], key=f"f_{st.session_state.selector_id}")
        
        with col2:
            c_f, c_h = st.columns(2)
            f_ar, h_ar = c_f.date_input("FECHA ARRIBO"), c_h.time_input("HORA ARRIBO", step=60)
            f_en, h_en = c_f.date_input("FECHA ENTRADA"), c_h.time_input("HORA ENTRADA", time(0,0), step=60)
            f_sa, h_sa = c_f.date_input("FECHA SALIDA"), c_h.time_input("HORA SALIDA", time(0,0), step=60)
            
            list_guardas = df_guardas['Nombre'].tolist() if not df_guardas.empty else ["Sin guardas"]
            guarda_sel = st.selectbox("GUARDA RESPONSABLE:", list_guardas)
            obs = st.text_area("OBSERVACIONES:", value=st.session_state.temp_datos["Obs"], key=f"o_{st.session_state.selector_id}")

        b1, b2, b3 = st.columns([2,1,1])
        if b1.button("💾 GUARDAR REGISTRO", type="primary"):
            dt_ar, dt_en, dt_sa = f"{f_ar} {h_ar.strftime('%H:%M')}", f"{f_en} {h_en.strftime('%H:%M')}", f"{f_sa} {h_sa.strftime('%H:%M')}"
            datos = {
                "ID": df_reg['ID'].max() + 1 if not df_reg.empty else 1,
                "Nombre": nombre, "Documento": documento, "Placa": placa, "Cliente": cliente,
                "Arribo": dt_ar, "Entrada": dt_en, "Salida": dt_sa, "Factura": factura,
                "Guarda": guarda_sel, "Observaciones": obs
            }
            # Update si existe, sino concat
            if not df_reg.empty and str(documento) in df_reg['Documento'].astype(str).values:
                for k, v in datos.items():
                    if k != "ID": df_reg.loc[df_reg['Documento'].astype(str) == str(documento), k] = v
                df_final = df_reg
            else:
                df_final = pd.concat([df_reg, pd.DataFrame([datos])], ignore_index=True)
            guardar_hoja(df_final, 'Registros')
            st.success("✅ Sincronizado")
            limpiar_todo()

        if b2.button("🗑️ ELIMINAR SELECCIONADO"):
            if "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
                idx_f = st.session_state.tabla_p.selection.rows[0]
                id_borrar = st.session_state.df_actual_p.iloc[idx_f]["ID"]
                df_final = df_reg[df_reg["ID"] != id_borrar]
                guardar_hoja(df_final, 'Registros')
                st.error("Registro Eliminado")
                limpiar_todo()

        if b3.button("🧹 LIMPIAR CAMPOS"):
            limpiar_todo()

    st.subheader("📋 TABLA GENERAL")
    search_p = st.text_input("🔍 FILTRO RÁPIDO:", key="search_p")
    df_display = df_reg.copy()
    if not df_display.empty:
        df_display['Arribo_DT'] = pd.to_datetime(df_display['Arribo'], errors='coerce')
        df_display = df_display.sort_values(by='Arribo_DT', ascending=False).drop(columns=['Arribo_DT'])
    
    if search_p:
        mask = df_display.astype(str).apply(lambda x: x.str.contains(search_p, case=False)).any(axis=1)
        df_display = df_display[mask]
    
    st.session_state.df_actual_p = df_display
    st.dataframe(df_display, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_p")

# ================= PÁGINA 2: GUARDAS =================
elif st.session_state.menu_sel == "Guardas":
    st.header("👮 Maestría de Guardas")
    df_g = cargar_hoja('Guardas')
    
    if "tabla_g" in st.session_state and st.session_state.tabla_g.selection.rows:
        idx = st.session_state.tabla_g.selection.rows[0]
        fila = df_g.iloc[idx]
        st.session_state.m_id, st.session_state.m_nom = str(fila["Empleado_ID"]), str(fila["Nombre"])

    with st.expander("📝 EDITAR / CREAR GUARDA", expanded=True):
        id_g = st.text_input("CÉDULA:", value=st.session_state.m_id, key=f"gi_{st.session_state.selector_id}")
        nom_g = st.text_input("NOMBRE COMPLETO:", value=st.session_state.m_nom, key=f"gn_{st.session_state.selector_id}")
        c1, c2 = st.columns(2)
        if c1.button("💾 GUARDAR GUARDA"):
            df_f = pd.concat([df_g[df_g['Empleado_ID'].astype(str) != str(id_g)], pd.DataFrame([{"Empleado_ID": id_g, "Nombre": nom_g}])], ignore_index=True)
            guardar_hoja(df_f, 'Guardas'); limpiar_todo()
        if c2.button("🗑️ BORRAR"):
            guardar_hoja(df_g[df_g['Empleado_ID'].astype(str) != str(id_g)], 'Guardas'); limpiar_todo()
    
    st.dataframe(df_g, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_g")

# ================= PÁGINA 3: TRANSPORTISTAS =================
elif st.session_state.menu_sel == "Transportistas":
    st.header("🚛 Maestría de Transportistas")
    df_t = cargar_hoja('Transportistas')
    
    if "tabla_t" in st.session_state and st.session_state.tabla_t.selection.rows:
        idx = st.session_state.tabla_t.selection.rows[0]
        fila = df_t.iloc[idx]
        st.session_state.m_id, st.session_state.m_nom = str(fila["ID_Transportista"]), str(fila["Nombre"])

    with st.expander("📝 EDITAR / CREAR TRANSPORTISTA", expanded=True):
        id_t = st.text_input("NIT / ID:", value=st.session_state.m_id, key=f"ti_{st.session_state.selector_id}")
        nom_t = st.text_input("NOMBRE TRANSPORTISTA:", value=st.session_state.m_nom, key=f"tn_{st.session_state.selector_id}")
        if st.button("💾 GUARDAR TRANSPORTISTA"):
            df_f = pd.concat([df_t[df_t['ID_Transportista'].astype(str) != str(id_t)], pd.DataFrame([{"ID_Transportista": id_t, "Nombre": nom_t, "Tipo": "FISICA"}])], ignore_index=True)
            guardar_hoja(df_f, 'Transportistas'); limpiar_todo()
    
    st.dataframe(df_t, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_t")

# ================= PÁGINA 4: REPORTES =================
elif st.session_state.menu_sel == "Reportes":
    st.header("📊 Centro de Descargas")
    df_rep = cargar_hoja('Registros')
    if not df_rep.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, sheet_name='Registros', index=False)
        st.download_button("📥 DESCARGAR EXCEL COMPLETO", data=output.getvalue(), file_name=f"Reporte_Flix_{datetime.now().strftime('%Y%m%d')}.xlsx", type="primary")
        st.dataframe(df_rep, use_container_width=True)
    else:
        st.warning("No hay datos para exportar.")