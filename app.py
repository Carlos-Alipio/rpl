import streamlit as st
import time

st.set_page_config(page_title="Login - Sistema RPL", page_icon="🔒", layout="centered")

# 1. Inicializa a Memória de Autenticação
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

# 2. Verifica se o utilizador já tem sessão iniciada
if st.session_state['autenticado']:
    st.title("Bem-vindo ao Sistema RPL - GLO ✈️")
    st.success("✅ Sessão iniciada com sucesso.")
    st.markdown("""
    **Acesso autorizado.** Utilize o menu lateral esquerdo para navegar:
    * **✈️ Gerador RPL:** Processar os planos de voo.
    * **⚙️ Configurações:** Gerir malha e aeroportos.
    """)
    
    # Botão de Logout
    st.write("")
    if st.button("🚪 Sair (Logout)"):
        st.session_state['autenticado'] = False
        st.rerun()

else:
    # 3. Desenha o Ecrã de Login
    st.title("🔒 Acesso Restrito")
    st.markdown("Por favor, inicie sessão para aceder ao sistema de gestão do RPL.")
    
    with st.container(border=True):
        with st.form("login_form"):
            usuario = st.text_input("Utilizador")
            senha = st.text_input("Palavra-passe", type="password")
            
            submit = st.form_submit_button("Entrar no Sistema", type="primary", use_container_width=True)
            
            if submit:
                # Verificação de credenciais (pode adicionar mais utilizadores aqui)
                if usuario.lower() == "admin" and senha == "glo2026":
                    st.session_state['autenticado'] = True
                    st.success("Acesso concedido! A redirecionar...")
                    time.sleep(1) # Pequena pausa para a mensagem ser lida
                    st.rerun()
                else:
                    st.error("❌ Utilizador ou palavra-passe incorretos.")