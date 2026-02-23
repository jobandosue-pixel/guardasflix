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
if "last_idx" not in st.session_state: st.session_state.last_idx = -1

if "temp_datos" not in st.session_state:
    st.session_state.temp_datos = {"Nombre": "", "Documento": "", "Placa": "", "Cliente": "", "Factura": "", "Obs": ""}
if "g_id" not in st.session_state: st.session_state.g_id = ""
if "g_nom" not in st.session_state: st.session_state.g_nom = ""
if "t_id" not in st.session_state: st.session_state.t_id = ""
if "t_nom" not in st.session_state: st.session_state.t_nom = ""

def limpiar_todo():
    st.session_state.temp_datos = {k: "" for k in st.session_state.temp_datos}
    st.session_state.g_id, st.session_state.g_nom = "", ""
    st.session_state.t_id, st.session_state.t_nom = "", ""
    st.session_state.last_idx = -1
    st.session_state.selector_id += 1
    st.rerun()

# ================= MENÚ LATERAL =================
with st.sidebar:
    st.markdown('<div class="titulo-flix">METALES FLIX</div>', unsafe_allow_html=True)
    st.divider()
    if st.button("🏠 LOGÍSTICA PRINCIPAL"): st.session_state.menu_sel = "Logística"; limpiar_todo()
    if st.button("👮 MAESTRO DE GUARDAS"): st.session_state.menu_sel = "Guardas"; limpiar_todo()
    if st.button("🚛 TRANSPORTISTAS"): st.session_state.menu_sel = "Transportistas"; limpiar_todo()
    if st.button("📊 REPORTES Y EXCEL"): st.session_state.menu_sel = "Reportes"; st.rerun()

# ================= PÁGINA 1: LOGÍSTICA =================
if st.session_state.menu_sel == "Logística":
    df_reg = cargar_hoja('Registros')
    df_transp = cargar_hoja('Transportistas')
    df_guardas = cargar_hoja('Guardas')

    st.header("🛸 Registro de Movimientos")

    with st.expander("➕ FORMULARIO DE REGISTRO", expanded=True):
        opciones_t = ["Digitación Manual"]
        if not df_transp.empty:
            opciones_t += (df_transp['Nombre'].astype(str) + " (" + df_transp['ID_Transportista'].astype(str) + ")").tolist()
        
        def al_seleccionar_t():
            sel = st.session_state[f"bus_t_{st.session_state.selector_id}"]
            if sel != "Digitación Manual":
                doc_id = sel.split('(')[-1].replace(')', '')
                match = df_transp[df_transp['ID_Transportista'].astype(str) == doc_id].iloc[0]
                st.session_state.temp_datos["Nombre"] = str(match['Nombre'])
                st.session_state.temp_datos["Documento"] = str(match['ID_Transportista'])
                st.session_state.selector_id += 1

        st.selectbox("🔍 BUSCAR TRANSPORTISTA MAESTRO:", opciones_t, key=f"bus_t_{st.session_state.selector_id}", on_change=al_seleccionar_t)
        st.divider()

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
        if b1.button("💾 GUARDAR / ACTUALIZAR", type="primary"):
            dt_ar, dt_en, dt_sa = f"{f_ar} {h_ar.strftime('%H:%M')}", f"{f_en} {h_en.strftime('%H:%M')}", f"{f_sa} {h_sa.strftime('%H:%M')}"
            datos = {"ID": df_reg['ID'].max()+1 if not df_reg.empty else 1, "Nombre": nombre, "Documento": documento, "Placa": placa, "Cliente": cliente, "Arribo": dt_ar, "Entrada": dt_en, "Salida": dt_sa, "Factura": factura, "Guarda": guarda_sel, "Observaciones": obs}
            if not df_reg.empty and str(documento) in df_reg['Documento'].astype(str).values:
                for k, v in datos.items(): 
                    if k != "ID": df_reg.loc[df_reg['Documento'].astype(str) == str(documento), k] = v
                df_f = df_reg
            else: df_f = pd.concat([df_reg, pd.DataFrame([datos])], ignore_index=True)
            guardar_hoja(df_f, 'Registros'); st.success("Sincronizado"); limpiar_todo()

        if b2.button("🗑️ BORRAR"):
            if "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
                # Usamos el DF original para borrar por ID real
                id_b = df_reg.iloc[st.session_state.tabla_p.selection.rows[0]]["ID"]
                guardar_hoja(df_reg[df_reg["ID"] != id_b], 'Registros'); limpiar_todo()

        if b3.button("🧹 LIMPIAR"): limpiar_todo()

    st.subheader("📋 MOVIMIENTOS REGISTRADOS")
    
    # --- BUSCADOR LOGÍSTICA ---
    busqueda_p = st.text_input("🔍 Filtrar por Nombre, Placa, Documento o Cliente:", key="bus_p")
    df_filtrado_p = df_reg[df_reg.apply(lambda row: busqueda_p.lower() in row.astype(str).str.lower().str.cat(sep=' '), axis=1)] if busqueda_p else df_reg
    
    event_p = st.dataframe(df_filtrado_p, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_p")

    if event_p.selection.rows:
        current_idx = event_p.selection.rows[0]
        # Obtenemos la fila del dataframe filtrado
        fila = df_filtrado_p.iloc[current_idx]
        if str(fila["Documento"]) != str(st.session_state.temp_datos["Documento"]):
            st.session_state.temp_datos = {"Nombre": str(fila["Nombre"]), "Documento": str(fila["Documento"]), "Placa": str(fila["Placa"]), "Cliente": str(fila["Cliente"]), "Factura": str(fila["Factura"]), "Obs": str(fila["Observaciones"])}
            st.session_state.selector_id += 1
            st.rerun()

# ================= PÁGINA 2: GUARDAS =================
elif st.session_state.menu_sel == "Guardas":
    st.header("👮 Maestro de Guardas")
    df_g = cargar_hoja('Guardas')

    with st.expander("📝 GESTIÓN DE GUARDAS", expanded=True):
        id_g_in = st.text_input("CÉDULA / ID:", value=st.session_state.g_id, key=f"gi_{st.session_state.selector_id}")
        nom_g_in = st.text_input("NOMBRE COMPLETO:", value=st.session_state.g_nom, key=f"gn_{st.session_state.selector_id}")
        c1, c2, c3 = st.columns([2,1,1])
        if c1.button("💾 GUARDAR / ACTUALIZAR"):
            df_f = pd.concat([df_g[df_g['Empleado_ID'].astype(str) != str(id_g_in)], pd.DataFrame([{"Empleado_ID": id_g_in, "Nombre": nom_g_in}])], ignore_index=True)
            guardar_hoja(df_f, 'Guardas'); limpiar_todo()
        if c2.button("🗑️ BORRAR"):
            guardar_hoja(df_g[df_g['Empleado_ID'].astype(str) != str(id_g_in)], 'Guardas'); limpiar_todo()
        if c3.button("🧹 LIMPIAR"): limpiar_todo()
    
    # --- BUSCADOR GUARDAS ---
    busqueda_g = st.text_input("🔍 Buscar Guarda por Nombre o ID:", key="bus_g")
    df_filtrado_g = df_g[df_g.apply(lambda row: busqueda_g.lower() in row.astype(str).str.lower().str.cat(sep=' '), axis=1)] if busqueda_g else df_g
    
    event_g = st.dataframe(df_filtrado_g, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_g")
    if event_g.selection.rows:
        fila_g = df_filtrado_g.iloc[event_g.selection.rows[0]]
        if str(fila_g["Empleado_ID"]) != st.session_state.g_id:
            st.session_state.g_id, st.session_state.g_nom = str(fila_g["Empleado_ID"]), str(fila_g["Nombre"])
            st.session_state.selector_id += 1
            st.rerun()

# ================= PÁGINA 3: TRANSPORTISTAS =================
elif st.session_state.menu_sel == "Transportistas":
    st.header("🚛 Maestro de Transportistas")
    df_t = cargar_hoja('Transportistas')

    with st.expander("📝 GESTIÓN DE TRANSPORTISTAS", expanded=True):
        id_t_in = st.text_input("NIT / ID:", value=st.session_state.t_id, key=f"ti_{st.session_state.selector_id}")
        nom_t_in = st.text_input("RAZÓN SOCIAL / NOMBRE:", value=st.session_state.t_nom, key=f"tn_{st.session_state.selector_id}")
        c1, c2, c3 = st.columns([2,1,1])
        if c1.button("💾 GUARDAR / ACTUALIZAR"):
            df_f = pd.concat([df_t[df_t['ID_Transportista'].astype(str) != str(id_t_in)], pd.DataFrame([{"ID_Transportista": id_t_in, "Nombre": nom_t_in, "Tipo": "FISICA"}])], ignore_index=True)
            guardar_hoja(df_f, 'Transportistas'); limpiar_todo()
        if c2.button("🗑️ BORRAR"):
            guardar_hoja(df_t[df_t['ID_Transportista'].astype(str) != str(id_t_in)], 'Transportistas'); limpiar_todo()
        if c3.button("🧹 LIMPIAR"): limpiar_todo()

    # --- BUSCADOR TRANSPORTISTAS ---
    busqueda_t = st.text_input("🔍 Buscar Transportista por Nombre o NIT:", key="bus_t")
    df_filtrado_t = df_t[df_t.apply(lambda row: busqueda_t.lower() in row.astype(str).str.lower().str.cat(sep=' '), axis=1)] if busqueda_t else df_t

    event_t = st.dataframe(df_filtrado_t, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_t")
    if event_t.selection.rows:
        fila_t = df_filtrado_t.iloc[event_t.selection.rows[0]]
        if str(fila_t["ID_Transportista"]) != st.session_state.t_id:
            st.session_state.t_id, st.session_state.t_nom = str(fila_t["ID_Transportista"]), str(fila_t["Nombre"])
            st.session_state.selector_id += 1
            st.rerun()

# ================= PÁGINA 4: REPORTES =================
elif st.session_state.menu_sel == "Reportes":
    st.header("📊 Centro de Descargas")
    df_rep = cargar_hoja('Registros')
    if not df_rep.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, sheet_name='Registros', index=False)
        st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Reporte_Flix.xlsx", type="primary")
        st.dataframe(df_rep, use_container_width=True)