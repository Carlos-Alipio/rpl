import streamlit as st
import pandas as pd
import bcrypt
from sqlalchemy import text

# ==========================================
# CONEXÃO COM O SUPABASE
# ==========================================
# O Streamlit gere a conexão automaticamente através do secrets.toml
conn = st.connection("supabase", type="sql")

# ==========================================
# GESTÃO DE ROTAS E AEROPORTOS (PANDAS + SQLALCHEMY)
# ==========================================
def get_rotas():
    try:
        # ttl=0 obriga o Streamlit a ignorar a memória e ir direto ao Supabase
        return conn.query("SELECT * FROM rotas", ttl=0)
    except Exception:
        # Se falhar, devolve a estrutura vazia para não quebrar a tela
        return pd.DataFrame(columns=['DE', 'PARA', 'MACH', 'FL', 'ROTA', 'EET', 'TV', 'HORA INICIO', 'HORA FIM'])

def get_aeroportos():
    try:
        return conn.query("SELECT * FROM aeroportos", ttl=0)
    except Exception:
        return pd.DataFrame(columns=['IATA', 'ICAO', 'CIDADE', 'ESTADO'])

def save_rotas(df):
    # O to_sql com o engine do SQLAlchemy cria ou atualiza a tabela automaticamente no Supabase
    df.to_sql('rotas', con=conn.engine, if_exists='replace', index=False)

def save_aeroportos(df):
    df.to_sql('aeroportos', con=conn.engine, if_exists='replace', index=False)

# ==========================================
# GESTÃO DE UTILIZADORES E SEGURANÇA
# ==========================================
def init_db():
    from sqlalchemy import text
    with conn.session as s:
        # 1. Tabela de Utilizadores (que já tem)
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                precisa_trocar_senha BOOLEAN DEFAULT TRUE
            )
        '''))
        
        # 2. NOVA: Tabela de Aeroportos
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS aeroportos (
                "IATA" TEXT,
                "ICAO" TEXT,
                "CIDADE" TEXT,
                "ESTADO" TEXT
            )
        '''))

        # 3. NOVA: Tabela de Rotas
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
    with conn.session as s:
        result = s.execute(text(
            "SELECT senha_hash, precisa_trocar_senha FROM usuarios WHERE email = :email"
        ), {"email": email.lower().strip()}).fetchone()

    if result:
        senha_hash, precisa_trocar = result
        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
            return True, precisa_trocar
    return False, False

def atualizar_senha(email, nova_senha):
    novo_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    with conn.session as s:
        s.execute(text(
            "UPDATE usuarios SET senha_hash = :hash, precisa_trocar_senha = FALSE WHERE email = :email"
        ), {"hash": novo_hash, "email": email.lower().strip()})
        s.commit()

def adicionar_usuario(email, senha_provisoria):
    hash_senha = bcrypt.hashpw(senha_provisoria.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        with conn.session as s:
            s.execute(text(
                "INSERT INTO usuarios (email, senha_hash, precisa_trocar_senha) VALUES (:email, :hash, TRUE)"
            ), {"email": email.lower().strip(), "hash": hash_senha})
            s.commit()
        return True
    except Exception:
        return False # E-mail já existe (Violação de Primary Key)

def get_usuarios():
    try:
        # O ttl=0 obriga o Streamlit a ir ao Supabase ler os dados frescos em tempo real
        return conn.query("SELECT email, precisa_trocar_senha FROM usuarios", ttl=0)
    except Exception:
        return pd.DataFrame(columns=['email', 'precisa_trocar_senha'])

def remover_usuario(email):
    with conn.session as s:
        s.execute(text("DELETE FROM usuarios WHERE email = :email"), {"email": email.lower().strip()})
        s.commit()

# Inicializa as tabelas de segurança no arranque
init_db()

