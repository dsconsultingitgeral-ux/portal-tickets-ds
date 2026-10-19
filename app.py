from datetime import date
import streamlit as st
from supabase import create_client, Client

st.set_page_config(page_title="Gestão | Digital Solutions", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

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
                st.error(f"Erro na ligação: {e}")
else:
    c1, c2 = st.columns([3, 1])
    c1.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}**")
    if c2.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("---")
    st.markdown("### 🕒 Módulo de Picagem de Ponto")
    st.write(f"Data de hoje: {date.today().strftime('%d/%m/%Y')}")

    # Consulta isolada e totalmente protegida contra qualquer erro de tabela/coluna
    registo = None
    try:
        r = supabase.table("picagens").select("*").eq("username", st.session_state.username).eq("data", str(date.today())).execute()
        if r and r.data:
            registo = r.data[0]
    except Exception as err:
        st.info("Tabela pronta a operar. Efetue a primeira marcação.")

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Registar Entrada 🟢", disabled=bool(registo and registo.get("hora_entrada"))):
            try:
                import datetime as dt
                hora_atual = dt.datetime.now().strftime("%H:%M:%S")
                if not registo:
                    supabase.table("picagens").insert({
                        "username": st.session_state.username, 
                        "data": str(date.today()), 
                        "hora_entrada": hora_atual
                    }).execute()
                st.success("Entrada registada com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao inserir: {e}")

    if registo:
        st.markdown(f"**Estado atual:** Entrada registada às {registo.get('hora_entrada')}")
    else:
        st.warning("Ainda não tem entrada registada para hoje.")
