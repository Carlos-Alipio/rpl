import streamlit as st
import pandas as pd
from db_utils import get_rotas, get_aeroportos, save_rotas, save_aeroportos

# Configuração da página
st.set_page_config(page_title="Configurações", page_icon="⚙️", layout="wide")

# --- CADEADO DE SEGURANÇA ---
if not st.session_state.get('autenticado', False):
    st.warning("🔒 Acesso Negado. Por favor, faça o login na página principal.")
    st.stop() 
# ----------------------------

# --- FUNÇÕES DE LIMPEZA E FORMATAÇÃO ---
def formatar_hora(t):
    """Garante que a hora lida da BD fica no formato HH:MM"""
    if pd.isna(t) or str(t).strip().lower() in ['nan', 'none', '']: return ""
    t_str = str(t).replace(':', '').replace('.0', '').strip()
    if t_str.isdigit():
        t_str = t_str.zfill(4)
        if len(t_str) == 4: return f"{t_str[:2]}:{t_str[2:]}"
    return str(t)

# --- GESTÃO DE ESTADO (MEMÓRIA DO SISTEMA) ---
def carregar_dados_memoria():
    # Carregar e limpar Rotas
    df_r = get_rotas()
    
    colunas_texto_r = ['DE', 'PARA', 'MACH', 'FL', 'ROTA', 'EET', 'TV']
    for col in colunas_texto_r:
        if col in df_r.columns:
            df_r[col] = df_r[col].apply(lambda x: str(x).upper().strip() if pd.notnull(x) else "")
            
    if 'HORA INICIO' in df_r.columns: df_r['HORA INICIO'] = df_r['HORA INICIO'].apply(formatar_hora)
    if 'HORA FIM' in df_r.columns: df_r['HORA FIM'] = df_r['HORA FIM'].apply(formatar_hora)
    df_r = df_r.reset_index(drop=True)
    st.session_state.df_rotas = df_r

    # Carregar e limpar Aeroportos
    df_a = get_aeroportos()
    
    df_a = df_a.loc[:, ~df_a.columns.str.contains('^Unnamed')]
    if 'IATA.1' in df_a.columns:
        df_a = df_a.drop(columns=['IATA.1'])
    
    if 'CIDADE' not in df_a.columns: df_a['CIDADE'] = ""
    if 'ESTADO' not in df_a.columns: df_a['ESTADO'] = ""
        
    colunas_texto_a = ['IATA', 'ICAO', 'CIDADE', 'ESTADO']
    for col in colunas_texto_a:
        if col in df_a.columns:
            df_a[col] = df_a[col].apply(lambda x: str(x).upper().strip() if pd.notnull(x) else "")
            
    df_a = df_a.reset_index(drop=True) 
    st.session_state.df_aeroportos = df_a

if 'df_rotas' not in st.session_state or 'df_aeroportos' not in st.session_state:
    carregar_dados_memoria()

st.header("⚙️ Painel de Configurações")
st.markdown("Gestão avançada da base de dados. Use os filtros para visualizar a malha e **clique diretamente numa linha da tabela** para a editar.")

aba1, aba2 = st.tabs(["🛣️ Gestão de Rotas", "🏢 Códigos de Aeroportos"])

# ==========================================
# ABA 1: ROTAS
# ==========================================
with aba1:
    # --- 1. FORMULÁRIO DE CRIAÇÃO ---
    st.subheader("1. Adicionar Nova Rota")
    with st.expander("➕ Clique aqui para preencher os dados de uma nova rota", expanded=False):
        with st.form("form_add_rota", clear_on_submit=True):
            c1, c2, c3, c4, c5 = st.columns(5)
            n_de = c1.text_input("DE (Origem)*", max_chars=4, help="Ex: SBSP")
            n_para = c2.text_input("PARA (Destino)*", max_chars=4, help="Ex: SBRJ")
            n_mach = c3.text_input("MACH", value="N0450")
            n_fl = c4.text_input("FL", max_chars=3, help="Ex: 350")
            n_tv = c5.text_input("TV (HH:MM)", value="00:00", max_chars=5, help="Tempo de Voo. Ex: 01:20")
            
            n_rota = st.text_area("ROTA*", help="Insira a rota completa.", height=100)
            
            # Ajuste de Layout: Horários juntos e Observações numa linha inteira em baixo
            c7, c8 = st.columns(2)
            n_h_inicio = c7.text_input("HORA INÍCIO (HH:MM)", max_chars=5)
            n_h_fim = c8.text_input("HORA FIM (HH:MM)", max_chars=5)
            
            n_eet = st.text_area("OBSERVAÇÕES (PBN/EET/EQPT)", help="Insira informações de EET, PBN, etc.", height=100)
            
            if st.form_submit_button("✅ Guardar Nova Rota na BD", type="primary"):
                if not n_de or not n_para or not n_rota:
                    st.error("⚠️ Os campos DE, PARA e ROTA são obrigatórios.")
                else:
                    nova_linha = {
                        "DE": n_de.upper().strip(), "PARA": n_para.upper().strip(), "MACH": n_mach.upper().strip(),
                        "FL": n_fl.upper().strip(), "ROTA": n_rota.upper().strip(), 
                        "TV": n_tv.replace(':', '').strip(), 
                        "HORA INICIO": n_h_inicio.strip(), "HORA FIM": n_h_fim.strip(), "EET": n_eet.upper().strip()
                    }
                    novo_df = pd.DataFrame([nova_linha])
                    
                    st.session_state.df_rotas = pd.concat([st.session_state.df_rotas, novo_df], ignore_index=True)
                    save_rotas(st.session_state.df_rotas) 
                    st.success("✅ Nova rota inserida com sucesso!")
                    st.rerun()

    st.divider()

    # --- 2. FILTROS E VISUALIZAÇÃO INTERATIVA ---
    st.subheader("2. Visualizar e Selecionar Malha")
    c_f1, c_f2, c_f3 = st.columns(3)
    
    opcoes_de = sorted(st.session_state.df_rotas['DE'].dropna().astype(str).unique())
    opcoes_para = sorted(st.session_state.df_rotas['PARA'].dropna().astype(str).unique())
    
    filtro_de = c_f1.multiselect("📍 Filtrar Origem (DE)", opcoes_de)
    filtro_para = c_f2.multiselect("📍 Filtrar Destino (PARA)", opcoes_para)
    filtro_rota = c_f3.text_input("🔍 Pesquisar trecho na ROTA")

    df_view = st.session_state.df_rotas.copy()
    if filtro_de: df_view = df_view[df_view['DE'].isin(filtro_de)]
    if filtro_para: df_view = df_view[df_view['PARA'].isin(filtro_para)]
    if filtro_rota: df_view = df_view[df_view['ROTA'].str.contains(filtro_rota, case=False, na=False)]

    if len(df_view) == 0:
        st.warning("Nenhuma rota encontrada com estes filtros.")
    else:
        st.info("👆 **Dica:** Clique na caixa de seleção à esquerda de qualquer linha na tabela para a editar ou apagar.")
        
        df_display = df_view.copy()
        if 'TV' in df_display.columns:
            df_display['TV'] = df_display['TV'].apply(formatar_hora)
            
        evento_selecao = st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True, 
            height=250,
            on_select="rerun",           
            selection_mode="single-row"  
        )
        
        st.divider()

        # --- 3. EDITOR DA ROTA SELECIONADA ---
        st.subheader("3. Gerir Rota Selecionada")
        
        linhas_clicadas = evento_selecao.selection.rows
        
        if not linhas_clicadas:
            st.warning("Nenhuma rota selecionada. Por favor, clique numa linha na tabela acima.")
        else:
            pos_idx = linhas_clicadas[0]
            idx_real = df_view.index[pos_idx]
            rota_atual = st.session_state.df_rotas.loc[idx_real]
            
            st.markdown(f"### A editar: `{rota_atual['DE']} ➡️ {rota_atual['PARA']}`")
            
            with st.form("form_gestao_rota"):
                c1, c2, c3, c4, c5 = st.columns(5)
                e_de = c1.text_input("DE*", value=rota_atual['DE'], max_chars=4)
                e_para = c2.text_input("PARA*", value=rota_atual['PARA'], max_chars=4)
                e_mach = c3.text_input("MACH", value=rota_atual['MACH'])
                e_fl = c4.text_input("FL", value=rota_atual['FL'], max_chars=3)
                e_tv = c5.text_input("TV (HH:MM)", value=formatar_hora(rota_atual['TV']), max_chars=5)
                
                e_rota = st.text_area("ROTA*", value=rota_atual['ROTA'], height=100)
                
                # Ajuste de Layout: Horários juntos e Observações numa linha inteira em baixo
                c7, c8 = st.columns(2)
                e_h_inicio = c7.text_input("HORA INÍCIO (HH:MM)", value=rota_atual['HORA INICIO'], max_chars=5)
                e_h_fim = c8.text_input("HORA FIM (HH:MM)", value=rota_atual['HORA FIM'], max_chars=5)
                
                eet_atual = "" if pd.isna(rota_atual.get('EET')) else str(rota_atual.get('EET')).strip()
                e_eet = st.text_area("OBSERVAÇÕES", value=eet_atual, height=100)
                
                st.write("") 
                col_btn_upd, col_btn_del = st.columns(2)
                
                btn_atualizar = col_btn_upd.form_submit_button("💾 Atualizar Dados", type="primary", use_container_width=True)
                btn_apagar = col_btn_del.form_submit_button("🗑️ Apagar esta Rota", use_container_width=True)
                
                if btn_atualizar:
                    if not e_de or not e_para or not e_rota:
                        st.error("⚠️ Os campos DE, PARA e ROTA são obrigatórios.")
                    else:
                        st.session_state.df_rotas.loc[idx_real, 'DE'] = e_de.upper().strip()
                        st.session_state.df_rotas.loc[idx_real, 'PARA'] = e_para.upper().strip()
                        st.session_state.df_rotas.loc[idx_real, 'MACH'] = e_mach.upper().strip()
                        st.session_state.df_rotas.loc[idx_real, 'FL'] = e_fl.upper().strip()
                        st.session_state.df_rotas.loc[idx_real, 'ROTA'] = e_rota.upper().strip()
                        st.session_state.df_rotas.loc[idx_real, 'TV'] = e_tv.replace(':', '').strip()
                        st.session_state.df_rotas.loc[idx_real, 'HORA INICIO'] = e_h_inicio.strip()
                        st.session_state.df_rotas.loc[idx_real, 'HORA FIM'] = e_h_fim.strip()
                        st.session_state.df_rotas.loc[idx_real, 'EET'] = e_eet.upper().strip()
                        
                        save_rotas(st.session_state.df_rotas)
                        st.success("✅ Rota atualizada com sucesso na Base de Dados!")
                        st.rerun()
                        
                elif btn_apagar:
                    st.session_state.df_rotas = st.session_state.df_rotas.drop(idx_real).reset_index(drop=True)
                    save_rotas(st.session_state.df_rotas)
                    st.warning("🗑️ Rota eliminada permanentemente da Base de Dados.")
                    st.rerun()

# ==========================================
# ABA 2: AEROPORTOS 
# ==========================================
with aba2:
    # --- 1. FORMULÁRIO DE CRIAÇÃO ---
    st.subheader("1. Adicionar Novo Aeroporto")
    with st.expander("➕ Clique aqui para registar um novo aeroporto", expanded=False):
        with st.form("form_add_aero", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
            n_iata = c1.text_input("IATA (3 Letras)*", max_chars=3, help="Ex: CGH")
            n_icao = c2.text_input("ICAO (4 Letras)*", max_chars=4, help="Ex: SBSP")
            n_cidade = c3.text_input("CIDADE", help="Ex: São Paulo")
            n_estado = c4.text_input("ESTADO", max_chars=2, help="Ex: SP")
            
            if st.form_submit_button("✅ Guardar Novo Aeroporto na BD", type="primary"):
                if not n_iata or not n_icao:
                    st.error("⚠️ Os campos IATA e ICAO são obrigatórios.")
                else:
                    nova_linha = {
                        "IATA": n_iata.upper().strip(), 
                        "ICAO": n_icao.upper().strip(),
                        "CIDADE": n_cidade.upper().strip(),
                        "ESTADO": n_estado.upper().strip()
                    }
                    novo_df = pd.DataFrame([nova_linha])
                    
                    st.session_state.df_aeroportos = pd.concat([st.session_state.df_aeroportos, novo_df], ignore_index=True)
                    save_aeroportos(st.session_state.df_aeroportos) 
                    st.success("✅ Novo aeroporto registado com sucesso!")
                    st.rerun()

    st.divider()

    # --- 2. FILTROS E VISUALIZAÇÃO INTERATIVA ---
    st.subheader("2. Pesquisar e Selecionar Aeroportos")
    filtro_aero = st.text_input("🔍 Pesquisar por IATA, ICAO, Cidade ou Estado (Ex: JPA, SBJP ou Paraíba)")
    
    df_view_aero = st.session_state.df_aeroportos.copy()
    
    if filtro_aero:
        filtro_upper = filtro_aero.upper().strip()
        df_view_aero = df_view_aero[
            df_view_aero['IATA'].str.contains(filtro_upper, na=False) | 
            df_view_aero['ICAO'].str.contains(filtro_upper, na=False) |
            df_view_aero['CIDADE'].str.contains(filtro_upper, na=False) |
            df_view_aero['ESTADO'].str.contains(filtro_upper, na=False)
        ]

    if len(df_view_aero) == 0:
        st.warning("Nenhum aeroporto encontrado.")
    else:
        st.info("👆 **Dica:** Tal como nas rotas, clique numa linha da tabela para a editar.")
        
        evento_selecao_aero = st.dataframe(
            df_view_aero, 
            use_container_width=True, 
            hide_index=True, 
            height=250,
            on_select="rerun",           
            selection_mode="single-row",
            key="tabela_aeroportos_view" 
        )
        
        st.divider()

        # --- 3. EDITOR DO AEROPORTO SELECIONADO ---
        st.subheader("3. Gerir Aeroporto Selecionado")
        
        linhas_clicadas_aero = evento_selecao_aero.selection.rows
        
        if not linhas_clicadas_aero:
            st.warning("Nenhum aeroporto selecionado. Por favor, clique numa linha na tabela acima.")
        else:
            pos_idx_aero = linhas_clicadas_aero[0]
            idx_real_aero = df_view_aero.index[pos_idx_aero]
            aero_atual = st.session_state.df_aeroportos.loc[idx_real_aero]
            
            st.markdown(f"### A editar conversão: `{aero_atual['IATA']} ➡️ {aero_atual['ICAO']}`")
            
            with st.form("form_gestao_aero"):
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                e_iata = c1.text_input("IATA*", value=aero_atual['IATA'], max_chars=3)
                e_icao = c2.text_input("ICAO*", value=aero_atual['ICAO'], max_chars=4)
                e_cidade = c3.text_input("CIDADE", value=aero_atual['CIDADE'])
                e_estado = c4.text_input("ESTADO", value=aero_atual['ESTADO'], max_chars=2)
                
                st.write("") 
                col_btn_upd, col_btn_del = st.columns(2)
                
                btn_atualizar_aero = col_btn_upd.form_submit_button("💾 Atualizar Dados", type="primary", use_container_width=True)
                btn_apagar_aero = col_btn_del.form_submit_button("🗑️ Apagar este Aeroporto", use_container_width=True)
                
                if btn_atualizar_aero:
                    if not e_iata or not e_icao:
                        st.error("⚠️ Os campos IATA e ICAO são obrigatórios.")
                    else:
                        st.session_state.df_aeroportos.loc[idx_real_aero, 'IATA'] = e_iata.upper().strip()
                        st.session_state.df_aeroportos.loc[idx_real_aero, 'ICAO'] = e_icao.upper().strip()
                        st.session_state.df_aeroportos.loc[idx_real_aero, 'CIDADE'] = e_cidade.upper().strip()
                        st.session_state.df_aeroportos.loc[idx_real_aero, 'ESTADO'] = e_estado.upper().strip()
                        
                        save_aeroportos(st.session_state.df_aeroportos)
                        st.success("✅ Aeroporto atualizado com sucesso na Base de Dados!")
                        st.rerun()
                        
                elif btn_apagar_aero:
                    st.session_state.df_aeroportos = st.session_state.df_aeroportos.drop(idx_real_aero).reset_index(drop=True)
                    save_aeroportos(st.session_state.df_aeroportos)
                    st.warning("🗑️ Aeroporto eliminado permanentemente da Base de Dados.")
                    st.rerun()