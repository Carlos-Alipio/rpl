import sqlite3
import pandas as pd

DB_PATH = 'database.sqlite'

def get_rotas():
    """Lê a tabela de rotas da base de dados e devolve um DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM rotas", conn)
    conn.close()
    return df

def get_aeroportos():
    """Lê a tabela de aeroportos da base de dados e devolve um DataFrame."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM aeroportos", conn)
    conn.close()
    return df

def save_rotas(df):
    """Guarda as alterações feitas na tabela de rotas."""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('rotas', conn, if_exists='replace', index=False)
    conn.close()

def save_aeroportos(df):
    """Guarda as alterações feitas na tabela de aeroportos."""
    conn = sqlite3.connect(DB_PATH)
    df.to_sql('aeroportos', conn, if_exists='replace', index=False)
    conn.close()