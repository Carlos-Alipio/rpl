import sqlite3
import pandas as pd

def setup_database():
    print("🚀 A iniciar a migração de dados para SQLite...")

    # 1. Criar a ligação ao banco de dados 
    # (Se o ficheiro não existir, o Python cria-o automaticamente)
    conn = sqlite3.connect('database.sqlite')

    try:
        # ==========================================
        # TABELA 1: AEROPORTOS (IATA -> ICAO)
        # ==========================================
        print("A processar a tabela de Aeroportos...")
        df_iata = pd.read_excel('IATA_ICAO.xlsx')
        
        # O Pandas faz a magia de criar a tabela SQL e inserir os dados de uma só vez
        df_iata.to_sql('aeroportos', conn, if_exists='replace', index=False)
        print(f"  -> {len(df_iata)} aeroportos guardados com sucesso.")

        # ==========================================
        # TABELA 2: ROTAS OPERACIONAIS
        # ==========================================
        print("A processar a tabela de Rotas...")
        df_rotas = pd.read_excel('Rotas.xlsx')
        
        # Limpamos os nomes das colunas antes de enviar para o banco de dados
        # para garantir que não temos problemas com espaços ou acentos no SQL
        df_rotas.rename(columns=lambda x: str(x).upper().strip().replace('Í', 'I').replace('í', 'I'), inplace=True)
        
        df_rotas.to_sql('rotas', conn, if_exists='replace', index=False)
        print(f"  -> {len(df_rotas)} rotas guardadas com sucesso.")

        print("\n✅ SUCESSO! O banco de dados 'database.sqlite' está pronto para ser utilizado.")

    except FileNotFoundError as e:
        print(f"\n❌ ERRO: Ficheiro não encontrado. Certifique-se de que os Excel estão na mesma pasta.")
        print(f"Detalhe do erro: {e}")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado: {e}")
    finally:
        # Fechar sempre a ligação para não corromper o ficheiro
        conn.close()

if __name__ == '__main__':
    setup_database()