import streamlit as st
import pandas as pd
import bcrypt
from sqlalchemy import text

# ==========================================
# CONEXÃO COM O SUPABASE (SEGURA)
# ==========================================
conn = st.connection(
    "supabase", 
    type="sql", 
    url=st.secrets["SUPABASE_URL"]
)

# ==========================================
# GESTÃO DE ROTAS E AEROPORTOS (PANDAS + SQLALCHEMY)
# ==========================================

def get_rotas():
    """Recupera todas as rotas com tratamento de erro e feedback ao utilizador."""
    try:
        df = conn.query("SELECT * FROM rotas", ttl=0)
        if df is None or df.empty:
            st.warning("Aviso: A tabela de rotas está vazia no banco de dados.")
            return pd.DataFrame(columns=['DE', 'PARA', 'MACH', 'FL', 'ROTA', 'EET', 'TV', 'HORA INICIO', 'HORA FIM'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar rotas: {e}")
        return pd.DataFrame(columns=['DE', 'PARA', 'MACH', 'FL', 'ROTA', 'EET', 'TV', 'HORA INICIO', 'HORA FIM'])

def get_aeroportos():
    """Recupera todos os aeroportos com tratamento de erro."""
    try:
        df = conn.query("SELECT * FROM aeroportos", ttl=0)
        if df is None or df.empty:
            st.warning("Aviso: A tabela de aeroportos está vazia.")
            return pd.DataFrame(columns=['IATA', 'ICAO', 'CIDADE', 'ESTADO'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar aeroportos: {e}")
        return pd.DataFrame(columns=['IATA', 'ICAO', 'CIDADE', 'ESTADO'])

def save_rotas(df):
    """Guarda as rotas usando TRUNCATE para preservar o schema e índices."""
    try:
        with conn.session as s:
            s.execute(text("TRUNCATE TABLE rotas"))
            s.commit()
        df.to_sql('rotas', con=conn.engine, if_exists='append', index=False)
        st.success("Rotas atualizadas com sucesso!")
    except Exception as e:
        st.error(f"Falha ao salvar rotas: {e}")

def save_aeroportos(df):
    """Guarda os aeroportos usando TRUNCATE para preservar o schema."""
    try:
        with conn.session as s:
            s.execute(text("TRUNCATE TABLE aeroportos"))
            s.commit()
        df.to_sql('aeroportos', con=conn.engine, if_exists='append', index=False)
        st.success("Aeroportos atualizados com sucesso!")
    except Exception as e:
        st.error(f"Falha ao salvar aeroportos: {e}")

# ==========================================
# GESTÃO DE UTILIZADORES E SEGURANÇA
# ==========================================

def init_db():
    """Inicializa o schema do banco de dados garantindo integridade dos tipos."""
    with conn.session as s:
        # 1. Tabela de Utilizadores (Corrigido: senha_hash)
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                precisa_trocar_senha BOOLEAN DEFAULT TRUE
            )
        '''))
        
        # 2. Tabela de Aeroportos
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS aeroportos (
                "IATA" TEXT,
                "ICAO" TEXT,
                "CIDADE" TEXT,
                "ESTADO" TEXT
            )
        '''))

        # 3. Tabela de Rotas
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS rotas (
                "DE" TEXT,
                "PARA" TEXT,
                "MACH" TEXT,
                "FL" TEXT,
                "ROTA" TEXT,
                "EET" TEXT,
                "TV" TEXT,
                "HORA INICIO" TEXT,
                "HORA FIM" TEXT
            )
        '''))
        s.commit()

def verificar_login(email, senha):
    """Verifica credenciais com hashing seguro."""
    try:
        with conn.session as s:
            query = text("SELECT senha_hash, precisa_trocar_senha FROM usuarios WHERE email = :email")
            result = s.execute(query, {"email": email.lower().strip()}).fetchone()

        if result:
            senha_hash, precisa_trocar = result
            if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
                return True, precisa_trocar
    except Exception as e:
        st.error(f"Erro na autenticação: {e}")
    return False, False

def atualizar_senha(email, nova_senha):
    """Atualiza a senha do utilizador e remove flag de troca obrigatória."""
    novo_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with conn.session as s:
            s.execute(text(
                "UPDATE usuarios SET senha_hash = :hash, precisa_trocar_senha = FALSE WHERE email = :email"
            ), {"hash": novo_hash, "email": email.lower().strip()})
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar senha: {e}")
        return False

def adicionar_usuario(email, senha_provisoria):
    """Cria novo utilizador com senha temporária."""
    hash_senha = bcrypt.hashpw(senha_provisoria.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with conn.session as s:
            s.execute(text(
                "INSERT INTO usuarios (email, senha_hash, precisa_trocar_senha) VALUES (:email, :hash, TRUE)"
            ), {"email": email.lower().strip(), "hash": hash_senha})
            s.commit()
        return True
    except Exception:
        return False # Provavelmente e-mail duplicado

def get_usuarios():
    """Lista utilizadores para o painel administrativo."""
    try:
        return conn.query("SELECT email, precisa_trocar_senha FROM usuarios", ttl=0)
    except Exception as e:
        st.error(f"Erro ao listar utilizadores: {e}")
        return pd.DataFrame(columns=['email', 'precisa_trocar_senha'])

def remover_usuario(email):
    """Remove utilizador do sistema."""
    try:
        with conn.session as s:
            s.execute(text("DELETE FROM usuarios WHERE email = :email"), {"email": email.lower().strip()})
            s.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao remover utilizador: {e}")
        return False

# Inicializa as tabelas no arranque do módulo
init_db()