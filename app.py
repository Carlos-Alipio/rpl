import streamlit as st
import time
from db_utils import verificar_login, atualizar_senha, init_db

# Garante que a base de dados acorda e se auto-repara mal a nuvem liga!
init_db()

# ==========================================
# 1. CONFIGURAÇÃO BASE E LOGÓTIPO
# ==========================================
st.set_page_config(
    page_title="Sistema RPL - GLO",
    page_icon="assets/logo-voegol-new.svg", # Muda o ícone na aba do navegador!
    layout="wide",
    initial_sidebar_state="expanded"
)

# Coloca a marca no topo do menu lateral (acima da navegação)
st.logo("assets/logo-voegol-new.svg")

# Estilização CSS injetada diretamente (Layout Premium)
st.markdown("""
    <style>
    /* Oculta o cabeçalho padrão do Streamlit para um visual mais limpo */
    header {visibility: hidden;}
    
    /* Botões primários mais elegantes */
    .stButton > button[data-baseweb="button"] {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Memória do Sistema de Segurança
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
    st.session_state['precisa_trocar_senha'] = False
    st.session_state['email_usuario'] = ""

# ==========================================
# TELA DE LOGIN (SEM MENU LATERAL)
# ==========================================
if not st.session_state['autenticado']:
    # Esconde o menu lateral obrigatoriamente
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    st.title("🔒 Login Sistema RPL")
    st.markdown("Insira o seu e-mail corporativo pré-autorizado para aceder à plataforma.")
    
    # Caixa centralizada para o formulário de login
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            with st.form("login_form"):
                email = st.text_input("E-mail corporativo", placeholder="exemplo@glo.com.br")
                senha = st.text_input("Palavra-passe", type="password")
                
                st.write("") # Espaço em branco
                submit = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
                
                if submit:
                    sucesso, precisa_trocar = verificar_login(email, senha)
                    if sucesso:
                        st.session_state['autenticado'] = True
                        st.session_state['precisa_trocar_senha'] = precisa_trocar
                        st.session_state['email_usuario'] = email.lower().strip()
                        st.rerun()
                    else:
                        st.error("❌ E-mail ou palavra-passe incorretos.")

# ==========================================
# USUÁRIO LOGADO
# ==========================================
else:
    # --- FASE A: TROCA DE SENHA OBRIGATÓRIA ---
    if st.session_state['precisa_trocar_senha']:
        # Mantém o menu escondido
        st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
        
        st.warning("⚠️ **Primeiro Acesso:** Por motivos de segurança corporativa, é obrigatório alterar a sua palavra-passe provisória.")
        
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            with st.form("form_troca_senha", border=True):
                nova_senha = st.text_input("Nova Palavra-passe", type="password", help="Mínimo de 6 caracteres")
                confirma_senha = st.text_input("Confirmar Nova Palavra-passe", type="password")
                
                st.write("")
                if st.form_submit_button("Atualizar e Entrar", type="primary", use_container_width=True):
                    if len(nova_senha) < 6:
                        st.error("A senha deve ter pelo menos 6 caracteres.")
                    elif nova_senha != confirma_senha:
                        st.error("As senhas não coincidem. Tente novamente.")
                    else:
                        atualizar_senha(st.session_state['email_usuario'], nova_senha)
                        st.session_state['precisa_trocar_senha'] = False
                        st.success("✅ Senha atualizada com sucesso! A redirecionar...")
                        time.sleep(1.5)
                        st.rerun()
                    
    # --- FASE B: SISTEMA PRINCIPAL COM MENU LATERAL ---
    else:
        # 1. Informação do utilizador no topo do menu lateral
        st.sidebar.markdown(f"👤 **{st.session_state['email_usuario']}**")
        
        # 2. Definição das Páginas (Mapeia para os ficheiros da pasta pages/)
        pg_rpl = st.Page("pages/1_✈️_Gerador_RPL.py", title="Gerador RPL", icon=":material/flight_takeoff:", default=True)
        pg_config = st.Page("pages/2_⚙️_Configuracoes.py", title="Configurações", icon=":material/settings:")

        # 3. Construção da Navegação Simples (Remove o espaço extra)
        pg = st.navigation([pg_rpl, pg_config])

        # 4. Roda a página selecionada
        pg.run()
        
        # 5. Botão de Logout no fundo do Sidebar
        st.sidebar.divider()
        if st.sidebar.button("Sair do Sistema", icon=":material/logout:", use_container_width=True):
            st.session_state['autenticado'] = False
            st.session_state['email_usuario'] = ""
            st.rerun()