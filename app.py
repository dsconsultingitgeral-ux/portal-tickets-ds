from datetime import datetime, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Gestão | Digital Solutions", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_supabase()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.nome = None
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.markdown("### Iniciar Sessão")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Entrar"):
            res = supabase.table("utilizadores").select("*").eq("username", u).execute()
            if res.data and res.data[0]["password"] == p:
                st.session_state.logged_in = True
                st.session_state.username = res.data[0]["username"]
                st.session_state.nome = res.data[0]["nome"]
                st.session_state.is_admin = "admin" in res.data[0]["username"].lower()
                st.rerun()
            else:
                st.error("Credenciais inválidas.")
else:
    col1, col2 = st.columns([3, 1])
    col1.markdown(f"👋 **{st.session_state.nome}**")
    if col2.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 Picagem de Ponto")
    st.write(f"Data: {date.today().strftime('%d/%m/%Y')}")

    # Bloco totalmente seguro com fallback para evitar qualquer erro de API
    registo = None
    try:
        res = supabase.table("picagens").select("*").eq("username", st.session_state.username).eq("data", str(date.today())).execute()
        if res and res.data:
            registo = res.data[0]
    except Exception:
        pass

    c1, c2, c3, c4 = st.columns(4)
    now = datetime.now().strftime("%H:%M:%S")

    if c1.button("Entrada 🟢", disabled=bool(registo and registo.get("hora_entrada"))):
        try:
            if not registo:
                supabase.table("picagens").insert({"username": st.session_state.username, "data": str(date.today()), "hora_entrada": now}).execute()
            else:
                supabase.table("picagens").update({"hora_entrada": now}).eq("id", registo["id"]).execute()
            st.rerun()
        except Exception as e:
            st.error(f"Erro: {e}")

    if registo:
        st.success(f"Entrada registada às {registo.get('hora_entrada')}")
    else:
        st.info("Ainda sem registo de entrada hoje.")
