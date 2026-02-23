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
    return True

# --- Control de Estado Crítico ---
if "menu_sel" not in st.session_state: st.session_state.menu_sel = "Logística"
if "selector_id" not in st.session_state: st.session_state.selector_id = 0

if "temp_datos" not in st.session_state:
    st.session_state.temp_datos = {"Nombre": "", "Documento": "", "Placa": "", "Cliente": "", "Factura": "", "Obs": ""}

if "m_id" not in st.session_state: st.session_state.m_id = ""
if "m_nom" not in st.session_state: st.session_state.m_nom = ""

def limpiar_todo():
    st.session_state.temp_datos = {k: "" for k in st.session_state.temp_datos}
    st.session_state.m_id = ""
    st.session_state.m_nom = ""
    st.session_state.selector_id += 1
    st.rerun()

# ================= MENÚ LATERAL =================
with st.sidebar:
    st.title("🛰️ METALES FLIX")
    if st.button("🏠 Logística Principal"):
        st.session_state.menu_sel = "Logística"; st.rerun()
    if st.button("👮 Maestro de Guardas"):
        st.session_state.menu_sel = "Guardas"; st.rerun()
    if st.button("🚛 Maestro de Transportistas"):
        st.session_state.menu_sel = "Transportistas"; st.rerun()
    if st.button("📊 Reportes y Excel"):
        st.session_state.menu_sel = "Reportes"; st.rerun()

# ================= PÁGINA 1: LOGÍSTICA =================
if st.session_state.menu_sel == "Logística":
    st.header("🛸 Control de Arribos y Salidas")
    df_reg = cargar_hoja('Registros')
    df_transp = cargar_hoja('Transportistas')
    df_guardas = cargar_hoja('Guardas')

    with st.expander("➕ FORMULARIO DE REGISTRO / EDICIÓN", expanded=True):
        opciones = ["Digitación Manual"]
        if not df_transp.empty:
            opciones += (df_transp['Nombre'].astype(str) + " (" + df_transp['ID_Transportista'].astype(str) + ")").tolist()
        
        def al_seleccionar_maestro():
            sel = st.session_state[f"bus_master_{st.session_state.selector_id}"]
            if sel != "Digitación Manual":
                doc_id = sel.split('(')[-1].replace(')', '')
                match = df_transp[df_transp['ID_Transportista'].astype(str) == doc_id].iloc[0]
                st.session_state.temp_datos["Nombre"] = str(match['Nombre'])
                st.session_state.temp_datos["Documento"] = str(match['ID_Transportista'])
                st.session_state.selector_id += 1 

        st.selectbox("BUSCAR EN MAESTRO:", opciones, key=f"bus_master_{st.session_state.selector_id}", on_change=al_seleccionar_maestro)
        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("NOMBRE COMPLETO:", value=st.session_state.temp_datos["Nombre"], key=f"n_{st.session_state.selector_id}")
            documento = st.text_input("DOCUMENTO DE IDENTIDAD:", value=st.session_state.temp_datos["Documento"], key=f"d_{st.session_state.selector_id}")
            placa = st.text_input("NÚMERO DE PLACA:", value=st.session_state.temp_datos["Placa"], key=f"p_{st.session_state.selector_id}")
            cliente = st.text_input("CLIENTE / DESTINO:", value=st.session_state.temp_datos["Cliente"], key=f"c_{st.session_state.selector_id}")
            factura = st.text_area("NÚMEROS DE FACTURA:", value=st.session_state.temp_datos["Factura"], key=f"f_{st.session_state.selector_id}")
        
        with col2:
            c_f, c_h = st.columns(2)
            f_ar, h_ar = c_f.date_input("FECHA ARRIBO"), c_h.time_input("HORA ARRIBO")
            f_en, h_en = c_f.date_input("FECHA ENTRADA"), c_h.time_input("HORA ENTRADA", time(0,0))
            f_sa, h_sa = c_f.date_input("FECHA SALIDA"), c_h.time_input("HORA SALIDA", time(0,0))
            list_guardas = df_guardas['Nombre'].tolist() if not df_guardas.empty else ["Sin guardas"]
            guarda_sel = st.selectbox("GUARDA EN TURNO:", list_guardas)
            obs = st.text_area("OBSERVACIONES:", value=st.session_state.temp_datos["Obs"], key=f"o_{st.session_state.selector_id}")

        b1, b2, b3 = st.columns([2,1,1])
        if b1.button("🚀 GUARDAR / ACTUALIZAR", type="primary"):
            dt_ar, dt_en, dt_sa = f"{f_ar} {h_ar.strftime('%H:%M')}", f"{f_en} {h_en.strftime('%H:%M')}", f"{f_sa} {h_sa.strftime('%H:%M')}"
            if not df_reg.empty and str(documento) in df_reg['Documento'].astype(str).values:
                df_reg.loc[df_reg['Documento'].astype(str) == str(documento), ["Nombre", "Placa", "Cliente", "Arribo", "Entrada", "Salida", "Factura", "Guarda", "Observaciones"]] = [nombre, placa, cliente, dt_ar, dt_en, dt_sa, factura, guarda_sel, obs]
                df_final = df_reg
            else:
                nuevo_id = df_reg['ID'].max() + 1 if not df_reg.empty else 1
                nueva_fila = pd.DataFrame([[nuevo_id, nombre, documento, placa, cliente, dt_ar, dt_en, dt_sa, factura, guarda_sel, obs]], columns=df_reg.columns)
                df_final = pd.concat([df_reg, nueva_fila], ignore_index=True)
            guardar_hoja(df_final, 'Registros'); st.success("✅ Guardado"); limpiar_todo()

        if b2.button("🗑️ ELIMINAR REGISTRO") and "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
            idx_f = st.session_state.tabla_p.selection.rows[0]
            # Usar los datos actuales de la tabla mostrada (ya ordenada y filtrada)
            search_p = st.session_state.get("search_p", "")
            df_view = df_reg.copy()
            if not df_view.empty:
                df_view['Arribo_DT'] = pd.to_datetime(df_view['Arribo'], errors='coerce')
                df_view = df_view.sort_values(by='Arribo_DT', ascending=False).drop(columns=['Arribo_DT'])
            
            if search_p:
                mask = df_view.astype(str).apply(lambda x: x.str.contains(search_p, case=False)).any(axis=1)
                df_view = df_view[mask]
            
            id_borrar = df_view.iloc[idx_f]["ID"]
            df_final = df_reg[df_reg["ID"] != id_borrar]
            guardar_hoja(df_final, 'Registros'); st.error("Registro eliminado"); limpiar_todo()

    st.subheader("📋 TABLA DE MOVIMIENTOS")
    search_p = st.text_input("🔍 FILTRAR TABLA (Nombre, Placa, Documento, Cliente...):", key="search_p")
    
    # --- Lógica de Ordenamiento por Fecha de Arribo ---
    df_display = df_reg.copy()
    if not df_display.empty:
        # Convertimos a datetime para ordenar correctamente, luego descartamos la columna auxiliar
        df_display['Arribo_DT'] = pd.to_datetime(df_display['Arribo'], errors='coerce')
        df_display = df_display.sort_values(by='Arribo_DT', ascending=False).drop(columns=['Arribo_DT'])

    if search_p:
        mask = df_display.astype(str).apply(lambda x: x.str.contains(search_p, case=False)).any(axis=1)
        df_display = df_display[mask]
    
    if "tabla_p" in st.session_state and st.session_state.tabla_p.selection.rows:
        idx_f = st.session_state.tabla_p.selection.rows[0]
        if idx_f < len(df_display):
            fila = df_display.iloc[idx_f]
            if st.session_state.temp_datos["Documento"] != str(fila["Documento"]):
                st.session_state.temp_datos = {"Nombre": str(fila["Nombre"]), "Documento": str(fila["Documento"]), "Placa": str(fila["Placa"]), "Cliente": str(fila["Cliente"]), "Factura": str(fila["Factura"]), "Obs": str(fila["Observaciones"])}
                st.session_state.selector_id += 1; st.rerun()

    st.dataframe(df_display, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_p")

# ================= PÁGINA 2: GUARDAS =================
elif st.session_state.menu_sel == "Guardas":
    st.header("👮 Maestro de Guardas")
    df_g = cargar_hoja('Guardas')
    
    search_g = st.text_input("🔍 FILTRAR GUARDAS:", key="search_g")
    df_g_filt = df_g.copy()
    if search_g:
        mask = df_g_filt.astype(str).apply(lambda x: x.str.contains(search_g, case=False)).any(axis=1)
        df_g_filt = df_g_filt[mask]

    if "tabla_g" in st.session_state and st.session_state.tabla_g.selection.rows:
        idx_f = st.session_state.tabla_g.selection.rows[0]
        if idx_f < len(df_g_filt):
            fila = df_g_filt.iloc[idx_f]
            if st.session_state.m_id != str(fila["Empleado_ID"]):
                st.session_state.m_id, st.session_state.m_nom = str(fila["Empleado_ID"]), str(fila["Nombre"])
                st.session_state.selector_id += 1; st.rerun()

    with st.expander("📝 GESTIÓN DE GUARDAS", expanded=True):
        col_id, col_nom = st.columns(2)
        id_g = col_id.text_input("ID / CÉDULA:", value=st.session_state.m_id, key=f"gi_{st.session_state.selector_id}")
        nom_g = col_nom.text_input("NOMBRE COMPLETO:", value=st.session_state.m_nom, key=f"gn_{st.session_state.selector_id}")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        if c1.button("💾 GUARDAR / ACTUALIZAR", type="primary"):
            if id_g and nom_g:
                if not df_g.empty and str(id_g) in df_g['Empleado_ID'].astype(str).values:
                    df_g.loc[df_g['Empleado_ID'].astype(str) == str(id_g), "Nombre"] = nom_g
                    df_final = df_g
                else:
                    df_final = pd.concat([df_g, pd.DataFrame([[id_g, nom_g]], columns=df_g.columns)], ignore_index=True)
                guardar_hoja(df_final, 'Guardas'); st.success("Guardado"); limpiar_todo()

        if c2.button("🗑️ BORRAR") and "tabla_g" in st.session_state and st.session_state.tabla_g.selection.rows:
            id_to_del = df_g_filt.iloc[st.session_state.tabla_g.selection.rows[0]]["Empleado_ID"]
            guardar_hoja(df_g[df_g["Empleado_ID"] != id_to_del], 'Guardas'); limpiar_todo()
        
        if c3.button("🧹 NUEVO"): limpiar_todo()

    st.dataframe(df_g_filt, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_g")

# ================= PÁGINA 3: TRANSPORTISTAS =================
elif st.session_state.menu_sel == "Transportistas":
    st.header("🚛 Maestro de Transportistas")
    df_t = cargar_hoja('Transportistas')
    
    search_t = st.text_input("🔍 FILTRAR TRANSPORTISTAS:", key="search_t")
    df_t_filt = df_t.copy()
    if search_t:
        mask = df_t_filt.astype(str).apply(lambda x: x.str.contains(search_t, case=False)).any(axis=1)
        df_t_filt = df_t_filt[mask]

    if "tabla_t" in st.session_state and st.session_state.tabla_t.selection.rows:
        idx_f = st.session_state.tabla_t.selection.rows[0]
        if idx_f < len(df_t_filt):
            fila = df_t_filt.iloc[idx_f]
            if st.session_state.m_id != str(fila["ID_Transportista"]):
                st.session_state.m_id, st.session_state.m_nom = str(fila["ID_Transportista"]), str(fila["Nombre"])
                st.session_state.selector_id += 1; st.rerun()

    with st.expander("📝 GESTIÓN DE TRANSPORTISTAS", expanded=True):
        col_id_t, col_nom_t = st.columns(2)
        id_t = col_id_t.text_input("ID / NIT:", value=st.session_state.m_id, key=f"ti_{st.session_state.selector_id}")
        nom_t = col_nom_t.text_input("NOMBRE:", value=st.session_state.m_nom, key=f"tn_{st.session_state.selector_id}")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        if c1.button("💾 GUARDAR / ACTUALIZAR", type="primary"):
            if id_t and nom_t:
                if not df_t.empty and str(id_t) in df_t['ID_Transportista'].astype(str).values:
                    df_t.loc[df_t['ID_Transportista'].astype(str) == str(id_t), "Nombre"] = nom_t
                    df_final = df_t
                else:
                    df_final = pd.concat([df_t, pd.DataFrame([[id_t, nom_t, "FISICA"]], columns=df_t.columns)], ignore_index=True)
                guardar_hoja(df_final, 'Transportistas'); st.success("Guardado"); limpiar_todo()

        if c2.button("🗑️ BORRAR") and "tabla_t" in st.session_state and st.session_state.tabla_t.selection.rows:
            id_to_del = df_t_filt.iloc[st.session_state.tabla_t.selection.rows[0]]["ID_Transportista"]
            guardar_hoja(df_t[df_t["ID_Transportista"] != id_to_del], 'Transportistas'); limpiar_todo()
            
        if c3.button("🧹 NUEVO"): limpiar_todo()

    st.dataframe(df_t_filt, use_container_width=True, on_select="rerun", selection_mode="single-row", key="tabla_t")

# ================= PÁGINA 4: REPORTES =================
elif st.session_state.menu_sel == "Reportes":
    st.header("📊 Exportación")
    df_rep = cargar_hoja('Registros')
    if not df_rep.empty:
        # También ordenamos los reportes para que el Excel salga ordenado
        df_rep['Arribo_DT'] = pd.to_datetime(df_rep['Arribo'], errors='coerce')
        df_rep = df_rep.sort_values(by='Arribo_DT', ascending=False).drop(columns=['Arribo_DT'])
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_rep.to_excel(writer, sheet_name='Registros', index=False)
        st.download_button("📥 DESCARGAR EXCEL", data=output.getvalue(), file_name="Logistica_Flix.xlsx", type="primary")
        st.dataframe(df_rep, use_container_width=True)