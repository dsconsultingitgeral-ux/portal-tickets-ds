import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st
from supabase import create_client, Client

# --- 1. CONFIGURAÇÃO DA PÁGINA (ESTILO CLEAN / APPLE) ---
st.set_page_config(
    page_title="Portal de Tickets | Digital Solutions",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Estilização CSS limpa e minimalista
st.markdown("""
    <style>
    .main {
        background-color: #fafafa;
    }
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
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    .ticket-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 4px solid #000000;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. LIGAÇÃO AO SUPABASE VIA SECRETS DO STREAMLIT ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# --- 3. FUNÇÃO DE ENVIO DE EMAIL (SMTP) ---
def enviar_email_ticket(ticket_id, cliente, topico, assunto, mensagem, email_cc):
    try:
        smtp_user = st.secrets["SMTP_EMAIL"]
        smtp_pass = st.secrets["SMTP_PASSWORD"]
        
        destinatarios = [smtp_user]
        if email_cc:
            cc_list = [e.strip() for e in email_cc.split(",")]
            destinatarios.extend(cc_list)

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = smtp_user
        msg['Subject'] = f"[#TK-{ticket_id}] Novo Ticket: {assunto} ({topico})"
        if email_cc:
            msg['Cc'] = email_cc

        corpo = f"""
        Foi submetido um novo ticket no Portal da Digital Solutions.
        
        - ID do Ticket: #TK-{ticket_id}
        - Cliente: {cliente}
        - Tópico: {topico}
        - Assunto: {assunto}
        
        Mensagem:
        {mensagem}
        
        --------------------------------------------------
        Digital Solutions & Consulting IT - Sistema Automático
        """
        msg.attach(MIMEText(corpo, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, destinatarios, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email automático: {e}")
        return False

# --- 4. LOGÓTIPO DA DIGITAL SOLUTIONS ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        st.image("logo.jpg", use_column_width=True)
    except Exception:
        pass

st.markdown("<p style='text-align: center; color: #86868b; margin-top: 5px; margin-bottom: 30px;'>Portal de Suporte e Gestão de Tickets</p>", unsafe_allow_html=True)

# --- 5. GESTÃO DE SESSÃO E LOGIN ---
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
            response = supabase.table("utilizadores").select("*").eq("username", username_input).execute()
            users = response.data
            
            if users and users[0]["password"] == password_input:
                user = users[0]
                
                if user.get("plataforma") in ["ticket", "tickets", "ambas"]:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.nome = user["nome"]
                    st.session_state.is_admin = "admin" in user["username"].lower()
                    st.rerun()
                else:
                    st.error("Este utilizador não tem permissão para aceder ao Portal de Tickets.")
            else:
                st.error("Username ou password incorretos.")

else:
    c_user, c_logout = st.columns([3, 1])
    with c_user:
        st.markdown(f"👋 **Bem-vindo, {st.session_state.nome}**")
    with c_logout:
        if st.button("Sair", key="btn_logout_main"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")

    # PERFIL ADMIN NA APP DE TICKETS
    if st.session_state.is_admin:
        st.markdown("### Painel de Gestão de Tickets (Admin)")
        st.markdown("Lista global de todos os tickets submetidos pelos clientes.")
        
        response = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        tickets = response.data
        
        if not tickets:
            st.info("Não existem tickets registados.")
        else:
            for t in tickets:
                t_id = t.get('id', '')
                t_cliente = t.get('username_cliente', '')
                t_topico = t.get('topico', '')
                t_assunto = t.get('assunto', '')
                t_msg = t.get('mensagem', '')
                t_cc = t.get('email_cc', '') if t.get('email_cc') else 'Nenhum'
                t_estado = t.get('estado', 'Aberto')
                status_color = "🟢" if t_estado == "Aberto" else "⚪"

                html_card = f"""
                    <div class="ticket-card">
                        <b>#TK-{t_id}</b> | <b>Cliente:</b> {t_cliente} | <b>Tópico:</b> {t_topico}<br>
                        <b>Assunto:</b> {t_assunto}<br>
                        <p style='color: #555; margin-top: 5px;'>{t_msg}</p>
                        <i>Email CC: {t_cc}</i><br>
                        <b>Estado atual:</b> {status_color} {t_estado}
                    </div>
                """
                st.markdown(html_card, unsafe_allow_html=True)
                
                if t_estado == "Aberto":
                    if st.button(f"Marcar #TK-{t_id} como Resolvido", key=f"btn_{t_id}"):
                        supabase.table("tickets").update({"estado": "Resolvido"}).eq("id", t_id).execute()
                        st.success(f"Ticket #TK-{t_id} resolvido com sucesso!")
                        st.rerun()
                st.markdown("---")

    # PERFIL CLIENTE NA APP DE TICKETS
    else:
        st.markdown("### Abrir Novo Ticket")
        with st.form("ticket_form", clear_on_submit=True):
            topico = st.selectbox("Selecione o Tópico", ["Bug", "Reunião para Novo Projeto", "Orçamentos", "Dúvidas", "Outros"])
            assunto = st.text_input("Assunto")
            mensagem = st.text_area("Mensagem (Máximo 500 caracteres)", max_chars=500, help="Descreva detalhadamente o seu pedido.")
            email_cc = st.text_input("Email em CC (Opcional - ex: colega@empresa.com)")
            
            submit_ticket = st.form_submit_button("Enviar Ticket")
            
            if submit_ticket:
                if not assunto or not mensagem:
                    st.warning("Por favor, preencha o assunto e a mensagem.")
                else:
                    data_insert = {
                        "username_cliente": st.session_state.username,
                        "topico": topico,
                        "assunto": assunto,
                        "mensagem": mensagem,
                        "email_cc": email_cc,
                        "estado": "Aberto"
                    }
                    res = supabase.table("tickets").insert(data_insert).execute()
                    
                    if res.data:
                        novo_id = res.data[0]["id"]
                        enviar_email_ticket(novo_id, st.session_state.username, topico, assunto, mensagem, email_cc)
                        st.success(f"Ticket #TK-{novo_id} criado com sucesso! Foi enviado um email de confirmação.")
                        st.rerun()

        st.markdown("---")
        st.markdown("### O seu Histórico de Tickets")
        
        response = supabase.table("tickets").select("*").eq("username_cliente", st.session_state.username).order("created_at", desc=True).execute()
        cli_tickets = response.data
        
        if not cli_tickets:
            st.info("Ainda não abriu nenhum ticket.")
        else:
            for t in cli_tickets:
                t_id = t.get('id', '')
                t_assunto = t.get('assunto', '')
                t_topico = t.get('topico', '')
                t_msg = t.get('mensagem', '')
                t_estado = t.get('estado', 'Aberto')
                status_color = "🟢" if t_estado == "Aberto" else "⚪"

                html_cli_card = f"""
                    <div class="ticket-card">
                        <b>#TK-{t_id}</b> - <b>{t_assunto}</b> ({t_topico})<br>
                        <p style='color: #555; margin-top: 5px;'>{t_msg}</p>
                        <b>Estado:</b> {status_color} {t_estado}
                    </div>
                """
                st.markdown(html_cli_card, unsafe_allow_html=True)
