from datetime import date, datetime
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
    st.markdown("### Iniciar Sessão - Gestão Interna")
    with st.form("login_form"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Entrar"):
            try:
                res = supabase.table("utilizadores").select("*").eq("username", u).execute()
                if res.data and res.data[0]["password"] == p:
                    st.session_state.logged_in = True
                    st.session_state.username = res.data[0]["username"]
                    st.session_state.nome = res.data[0]["nome"]
                    st.session_state.is_admin = "admin" in res.data[0]["username"].lower()
                    st.rerun()
                else:
                    st.error("Utilizador ou password incorretos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")
else:
    c1, c2 = st.columns([3, 1])
    c1.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}**")
    if c2.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 Picagem de Ponto Diária")
    hoje_str = str(date.today())
    st.write(f"Data: {date.today().strftime('%d/%m/%Y')}")

    registo = None
    try:
        # Consulta totalmente isolada com captura de qualquer erro da base de dados
        res_ponto = supabase.table("picagens").select("*").eq("username", st.session_state.username).eq("data", hoje_str).execute()
        if res_ponto and res_ponto.data:
            registo = res_ponto.data[0]
    except Exception as e:
        st.error(f"⚠️ Erro detalhado retornado pelo Supabase: {e}")

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    now_time = datetime.now().strftime("%H:%M:%S")

    with col_p1:
        if st.button("Entrada 🟢", disabled=bool(registo and registo.get("hora_entrada"))):
            try:
                if not registo:
                    supabase.table("picagens").insert({
                        "username": st.session_state.username,
                        "data": hoje_str,
                        "hora_entrada": now_time
                    }).execute()
                else:
                    supabase.table("picagens").update({"hora_entrada": now_time}).eq("id", registo["id"]).execute()
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao inserir entrada: {e}")

    if registo:
        st.success(f"Entrada registada às {registo.get('hora_entrada')}")
    else:
        st.info("Ainda não tem entrada registada hoje.")
