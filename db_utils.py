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
        # conn.query já devolve um DataFrame do Pandas!
        return conn.query("SELECT * FROM rotas")
    except Exception:
        return pd.DataFrame() # Retorna vazio se a tabela ainda não existir

def get_aeroportos():
    try:
        return conn.query("SELECT * FROM aeroportos")
    except Exception:
        return pd.DataFrame()

def save_rotas(df):
    # O to_sql com o engine do SQLAlchemy cria ou atualiza a tabela automaticamente no Supabase
    df.to_sql('rotas', con=conn.engine, if_exists='replace', index=False)

def save_aeroportos(df):
    df.to_sql('aeroportos', con=conn.engine, if_exists='replace', index=False)

# ==========================================
# GESTÃO DE UTILIZADORES E SEGURANÇA
# ==========================================
def init_db():
    """Cria a tabela de utilizadores no Supabase e o admin padrão."""
    with conn.session as s:
        # Usa o tipo BOOLEAN verdadeiro do PostgreSQL
        s.execute(text('''
            CREATE TABLE IF NOT EXISTS usuarios (
                email TEXT PRIMARY KEY,
                senha_hash TEXT NOT NULL,
                precisa_trocar_senha BOOLEAN NOT NULL
            )
        '''))
        
        # Verifica se o Admin existe
        res = s.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        if res == 0:
            senha_padrao = bcrypt.hashpw("glo2026".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            s.execute(text(
                "INSERT INTO usuarios (email, senha_hash, precisa_trocar_senha) VALUES (:email, :senha, TRUE)"
            ), {"email": "admin@glo.com.br", "senha": senha_padrao})
        
        s.commit() # Confirma as alterações na base de dados

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