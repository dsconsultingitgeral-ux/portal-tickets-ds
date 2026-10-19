from datetime import date, datetime
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão e Operações | Digital Solutions",
    page_icon="⚙️",
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

st.markdown("<p style='text-align: center; color: #86868b; margin-top: 5px; margin-bottom: 25px;'>Portal de Gestão & Operações Internas</p>", unsafe_allow_html=True)

# --- 4. GESTÃO DE SESSÃO E LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.nome = None
    st.session_state.is_admin = False

if not st.session_state.logged_in:
    st.markdown("### Iniciar Sessão")
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
                    if user.get("plataforma") in ["gestao", "ambas"]:
                        st.session_state.logged_in = True
                        st.session_state.username = user["username"]
                        st.session_state.nome = user["nome"]
                        st.session_state.is_admin = "admin" in user["username"].lower()
                        st.rerun()
                    else:
                        st.error("Este utilizador não tem permissão para aceder à plataforma de Gestão.")
                else:
                    st.error("Username ou password incorretos.")
            except Exception as e:
                st.error(f"Erro no login: {e}")

else:
    c_user, c_logout = st.columns([3, 1])
    with c_user:
        st.markdown(f"👋 **Bem-vindo(a), {st.session_state.nome}**")
    with c_logout:
        if st.button("Sair", key="btn_logout_main"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    # Separadores sem a Picagem de Ponto
    tabs = st.tabs(["📁 Projetos & Horas", "🏖️ Férias e Ausências", "👑 Painel Admin"] if st.session_state.is_admin else ["📁 Projetos & Horas", "🏖️ Férias e Ausências"])
    hoje_str = date.today().strftime("%Y-%m-%d")

    # ==========================================
    # TAB 1: PROJETOS E HORAS
    # ==========================================
    with tabs[0]:
        st.markdown("### Registo de Horas em Projetos")
        projetos = []
        try:
            res_proj = supabase.table("projetos").select("*").eq("estado", "Ativo").execute()
            projetos = res_proj.data if res_proj and res_proj.data else []
        except Exception as e:
            st.warning(f"Não foi possível carregar os projetos: {e}")

        if not projetos:
            st.info("Não existem projetos ativos disponíveis de momento.")
        else:
            options_proj = {p["nome_projeto"]: p["id"] for p in projetos}
            with st.form("form_horas"):
                proj_nome = st.selectbox("Selecione o Projeto", list(options_proj.keys()))
                horas = st.number_input("Horas Dedicadas", min_value=0.5, max_value=24.0, step=0.5)
                descricao = st.text_area("Descrição do Trabalho Efetuado")
                sub_horas = st.form_submit_button("Registar Horas")
                
                if sub_horas:
                    if not descricao:
                        st.warning("Descreva o trabalho efetuado.")
                    else:
                        try:
                            data_h = {
                                "projeto_id": options_proj[proj_nome],
                                "username": st.session_state.username,
                                "data": hoje_str,
                                "horas_dedicadas": horas,
                                "descricao": descricao
                            }
                            supabase.table("projetos_horas").insert(data_h).execute()
                            st.success("Horas registadas com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao registar horas: {e}")

        st.markdown("---")
        st.markdown("### Os Seus Registos Recentes")
        try:
            res_meus_reg = supabase.table("projetos_horas").select("*, projetos(nome_projeto)").eq("username", st.session_state.username).order("data", desc=True).limit(10).execute()
            if res_meus_reg and res_meus_reg.data:
                df_h = pd.DataFrame(res_meus_reg.data)
                st.dataframe(df_h[["data", "horas_dedicadas", "descricao"]], use_container_width=True)
        except Exception:
            st.info("Sem registos de horas.")

    # ==========================================
    # TAB 2: FÉRIAS E AUSÊNCIAS
    # ==========================================
    with tabs[1]:
        st.markdown("### Marcar Férias ou Ausência")
        with st.form("form_ferias"):
            tipo_ausencia = st.selectbox("Tipo de Ausência", ["Férias", "Doença", "Formação", "Outros"])
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                dt_ini = st.date_input("Data de Início", min_value=date.today())
            with c_d2:
                dt_fim = st.date_input("Data de Fim", min_value=date.today())
            
            obs = st.text_input("Observações (Opcional)")
            sub_ferias = st.form_submit_button("Submeter Pedido")
            
            if sub_ferias:
                if dt_fim < dt_ini:
                    st.error("A data de fim não pode ser anterior à data de início.")
                else:
                    try:
                        dias = (dt_fim - dt_ini).days + 1
                        data_f = {
                            "username": st.session_state.username,
                            "tipo": tipo_ausencia,
                            "data_inicio": dt_ini.strftime("%Y-%m-%d"),
                            "data_fim": dt_fim.strftime("%Y-%m-%d"),
                            "dias_uteis": dias,
                            "estado": "Pendente",
                            "observacoes": obs
                        }
                        supabase.table("ferias").insert(data_f).execute()
                        st.success("Pedido submetido com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao submeter pedido: {e}")

        st.markdown("---")
        st.markdown("### Histórico de Pedidos de Férias")
        try:
            res_minhas_ferias = supabase.table("ferias").select("*").eq("username", st.session_state.username).order("created_at", desc=True).execute()
            if res_minhas_ferias and res_minhas_ferias.data:
                for f in res_minhas_ferias.data:
                    cor_est = "🟡" if f["estado"] == "Pendente" else ("🟢" if f["estado"] == "Aprovado" else "🔴")
                    st.markdown(f"""
                        <div class="card-box">
                            <b>Tipo:</b> {f['tipo']} | <b>De:</b> {f['data_inicio']} <b>Até:</b> {f['data_fim']} ({f['dias_uteis']} dias)<br>
                            <b>Estado:</b>
