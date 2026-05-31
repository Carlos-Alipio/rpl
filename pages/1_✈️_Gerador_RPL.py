import streamlit as st
import pandas as pd
import os
from core import gerar_ficheiros_rpl

st.set_page_config(page_title="Gerador RPL", page_icon="🖨️")

# --- CADEADO DE SEGURANÇA ---
if not st.session_state.get('autenticado', False):
    st.warning("🔒 Acesso Negado. Por favor, faça o login na página principal.")
    st.stop() # Mata a execução da página aqui mesmo!
# ----------------------------

st.header("🖨️ Gerador de RPL")
st.markdown("Insira o ficheiro mensal de voos e escolha o período de validade para o processamento.")

# --- MEMÓRIA DO STREAMLIT (SESSION STATE) ---
# Inicializamos as variáveis na memória para que ele não se esqueça dos ficheiros
if 'rpl_processado' not in st.session_state:
    st.session_state['rpl_processado'] = False
    st.session_state['txt_path'] = None
    st.session_state['csv_path'] = None

# 1. Área de Upload
ficheiro_csv = st.file_uploader("Ficheiro da Malha de Voos (CSV)", type=['csv'])

st.divider()

# 2. Escolha de Datas
st.subheader("Período de Validade")
col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data de Início")
with col2:
    data_fim = st.date_input("Data de Fim")

st.divider()

# 3. Botão de Ação (Apenas gera e guarda na memória)
if st.button("🚀 Processar RPL", type="primary", use_container_width=True):
    if ficheiro_csv is None:
        st.error("⚠️ Por favor, faça o upload do ficheiro CSV primeiro.")
    elif data_inicio > data_fim:
        st.error("⚠️ A data de início não pode ser posterior à data de fim.")
    else:
        with st.spinner("A cruzar dados com a base de rotas... Por favor, aguarde."):
            try:
                txt_path, csv_path = gerar_ficheiros_rpl(
                    caminho_csv_voos=ficheiro_csv, 
                    data_inicio_str=data_inicio.strftime('%Y-%m-%d'), 
                    data_fim_str=data_fim.strftime('%Y-%m-%d')
                )
                
                # GUARDAR RESULTADOS NA MEMÓRIA!
                st.session_state['txt_path'] = txt_path
                st.session_state['csv_path'] = csv_path
                st.session_state['rpl_processado'] = True
                
            except Exception as e:
                st.error(f"❌ Ocorreu um erro técnico durante o processamento: {e}")

# 4. Exibir Botões de Download (Fora do if processar!)
# Como está fora do bloco do botão, ficará sempre visível enquanto a variável de memória for True
if st.session_state['rpl_processado']:
    st.success("✅ Ficheiros gerados com sucesso e perfeitamente formatados para o CGNA!")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with open(st.session_state['txt_path'], "rb") as f_txt:
        col_btn1.download_button(
            label="📥 Descarregar RPL_Final.txt",
            data=f_txt,
            file_name=f"RPL_GLO_{data_inicio.strftime('%d%m%y')}.txt",
            mime="text/plain",
            use_container_width=True
        )
        
    with open(st.session_state['csv_path'], "rb") as f_csv:
        col_btn2.download_button(
            label="📊 Descarregar Planilha CSV",
            data=f_csv,
            file_name=f"RPL_Dados_{data_inicio.strftime('%d%m%y')}.csv",
            mime="text/csv",
            use_container_width=True
        )