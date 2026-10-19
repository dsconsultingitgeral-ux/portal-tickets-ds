from datetime import datetime
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Portal de Tickets | Digital Solutions",
    page_icon="🎫",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    .main { background-color: #fafafa; }
    h1, h2, h3 {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #1d1d1f;
    }
    .stButton>button {
        background-color: #000000;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    .stButton>button:hover { background-color: #333333; color: white; }
    .card-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 20px;
        border: 1px solid #e5e5ea;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIGAÇÃO AO SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# --- 3. LOGÓTIPO ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("logo.jpg", use_column_width=True)
    except Exception:
        pass

st.markdown("<p style='text-align: center; color: #86868b; margin-top: 5px; margin-bottom: 25px;'>Portal de Suporte & Tickets Internos</p>", unsafe_allow_html=True)

# --- 4. GESTÃO DE SESSÃO E LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.nome = None
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.markdown("### Iniciar Sessão - Tickets")
    with st.form("login_form"):
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            try:
                response = supabase.table("utilizadores").select("*").eq("username", username_input).execute()
                users = response.data
                
                if users and users[0]["password"] == password_input:
                    user = users[0]
                    if user.get("plataforma") in ["tickets", "ambas"]:
                        st.session_state.logged_in = True
                        st.session_state.username = user["username"]
                        st.session_state.nome = user["nome"]
                        st.session_state.is_admin = "admin" in user["username"].lower()
                        st.rerun()
                    else:
                        st.error("Este utilizador não tem permissão para aceder ao Portal de Tickets.")
                else:
                    st.error("Username ou password incorretos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")

else:
    c_user, c_logout = st.columns([3, 1])
    with c_user:
        st.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}**")
    with c_logout:
        if st.button("Sair", key="btn_logout_tickets"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    tabs = st.tabs(["➕ Criar Ticket", "📋 Meus Tickets", "👑 Painel Admin"] if st.session_state.is_admin else ["➕ Criar Ticket", "📋 Meus Tickets"])

    # --- TAB 1: CRIAR TICKET ---
    with tabs[0]:
        st.markdown("### Abrir Novo Ticket")
        with st.form("form_ticket"):
            titulo = st.text_input("Título / Assunto")
            categoria = st.selectbox("Categoria", ["Suporte Técnico", "Hardware", "Software", "Acessos", "Outros"])
            prioridade = st.selectbox("Prioridade", ["Baixa", "Média", "Alta", "Urgente"])
            descricao = st.text_area("Descrição Detalhada")
            sub_ticket = st.form_submit_button("Submeter Ticket")

            if sub_ticket:
                if not titulo or not descricao:
                    st.warning("Por favor preencha o título e a descrição.")
                else:
                    try:
                        novo_t = {
                            "username": st.session_state.username,
                            "titulo": titulo,
                            "categoria": categoria,
                            "prioridade": prioridade,
                            "descricao": descricao,
                            "estado": "Aberto"
                        }
                        supabase.table("tickets").insert(novo_t).execute()
                        st.success("Ticket criado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao submeter ticket: {e}")

    # --- TAB 2: MEUS TICKETS ---
    with tabs[1]:
        st.markdown("### Os Seus Tickets")
        try:
            res_tk = supabase.table("tickets").select("*").eq("username", st.session_state.username).order("created_at", desc=True).execute()
            if res_tk and res_tk.data:
                for tk in res_tk.data:
                    estado_atual = tk.get("estado", "Aberto")
                    cor_st = "🟡" if estado_atual == "Aberto" else ("🔵" if estado_atual == "Em Resolução" else "🟢")
                    
                    t_id = tk.get('id', '')
                    t_titulo = tk.get('titulo', '')
                    t_cat = tk.get('categoria', '')
                    t_prio = tk.get('prioridade', '')
                    t_desc = tk.get('descricao', '')

                    st.markdown(f"""
                        <div class="card-box">
                            <b>#{t_id} - {t_titulo}</b> | Categoria: {t_cat} | Prioridade: {t_prio}<br>
                            <b>Estado:</b> {cor_st} {estado_atual}<br>
                            <p style="margin-top:8px; color:#424245;">{t_desc}</p>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Ainda não submeteu nenhum ticket.")
        except Exception as e:
            st.error(f"Erro ao carregar tickets: {e}")

    # --- TAB 3: PAINEL ADMIN ---
    if st.session_state.is_admin:
        with tabs[2]:
            st.markdown("### Gestão de Tickets (Admin)")
            try:
                res_all = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
                if res_all and res_all.data:
                    for tk in res_all.data:
                        estado_atual = tk.get("estado", "Aberto")
                        t_id = tk.get('id', '')
                        t_titulo = tk.get('titulo', '')
                        t_user = tk.get('username', '')
                        t_cat = tk.get('categoria', '')
                        t_prio = tk.get('prioridade', '')
                        t_desc = tk.get('descricao', '')

                        st.markdown(f"""
                            <div class="card-box">
                                <b>#{t_id} - {t_titulo}</b> ({t_user})<br>
                                <b>Categoria:</b> {t_cat} | <b>Prioridade:</b> {t_prio}<br>
                                <b>Estado Atual:</b> {estado_atual}<br>
                                <p style="margin-top:8px; color:#424245;">{t_desc}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        c_a1, c_a2 = st.columns(2)
                        with c_a1:
                            if st.button(f"Em Resolução #{t_id}", key=f"resolv_{t_id}"):
                                supabase.table("tickets").update({"estado": "Em Resolução"}).eq("id", t_id).execute()
                                st.rerun()
                        with c_a2:
                            if st.button(f"Fechar #{t_id}", key=f"fechar_{t_id}"):
                                supabase.table("tickets").update({"estado": "Fechado"}).eq("id", t_id).execute()
                                st.rerun()
                else:
                    st.info("Não existem tickets registados.")
            except Exception as e:
                st.error(f"Erro no painel admin: {e}")
