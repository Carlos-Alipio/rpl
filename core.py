import pandas as pd
import streamlit as st
import textwrap
from datetime import datetime
import os

# ==========================================
# CONSTANTES E CONFIGURAÇÕES (CLEAN CODE)
# ==========================================
DEFAULT_RMK_1 = "EQPT/SDFGIKRWY/LB1 STS/ATFMX"
DEFAULT_RMK_2 = "PBN/B1C1D1O1S2T1 EET/SBCW0003"
DEFAULT_ROUTE = "N0000 000 ROUTE UNKNOWN"
PREFIXOS_BR = ('SB', 'SD', 'SI', 'SJ', 'SN', 'SS', 'SW')

# ==========================================
# FUNÇÕES AUXILIARES DE FORMATAÇÃO E ROTAS
# ==========================================
def parse_time_to_int(t_str):
    if pd.isna(t_str) or str(t_str).strip().lower() in ['nan', 'none', '']: return None
    try: return int(str(t_str).replace(':', '').strip())
    except ValueError: return None

def parse_rmk(rmk_raw):
    """Extrai informações de observações com valores padrão centralizados."""
    if pd.isna(rmk_raw):
        return DEFAULT_RMK_1, DEFAULT_RMK_2
    
    rmk_str = str(rmk_raw).strip()
    if rmk_str.lower() in ['nan', 'none', '', '<na>']:
        return DEFAULT_RMK_1, DEFAULT_RMK_2
    
    if 'PBN/' in rmk_str:
        idx = rmk_str.find('PBN/')
        return rmk_str[:idx].strip(), rmk_str[idx:].strip()
    elif 'EET/' in rmk_str and 'EQPT/' not in rmk_str:
        return "", rmk_str
    elif 'EET/' in rmk_str and 'EQPT/' in rmk_str:
        idx = rmk_str.find('EET/')
        return rmk_str[:idx].strip(), rmk_str[idx:].strip()
    else:
        return rmk_str, ""

def map_equipment(eq):
    eq = str(eq).strip().upper()
    if eq == "73G": return "B737/M"
    elif eq in ["73M", "73X", "738", "73A"]: return "B738/M"
    elif eq in ["7M8", "7ME"]: return "B38M/M"
    else: return "B738/M" 

def gerar_cabecalho(data_ref, pagina_atual):
    meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    data_formatada = f"{data_ref.day:02d}{meses[data_ref.month-1]}.{data_ref.year}"
    
    linhas_cabecalho = []
    if pagina_atual == 1:
        linhas_cabecalho.extend(["", "", "                                               Planos de Voo Repetitivos", "                                               Classificação: Ident Anv", ""])
    else:
        linhas_cabecalho.extend(["", ""]) 

    linhas_cabecalho.extend([
        f"CIA: GLO                                    INÍCIO DE VALIDADE: {data_formatada}                                       PAG.: {pagina_atual}",
        "-----------------------------------------------------------------------------------------------------------------------------------------",
        "   VALIDO VALIDO DIAS OP  IDENT  TIPO   ADEP     VEL   FL  ROTA                                DEST         OBSERVACOES",
        "   DESDE   ATE   STQQSSD   ANV     TURB     EOBT                                                   EET",
        "-----------------------------------------------------------------------------------------------------------------------------------------",
        "", ""  
    ])
    return linhas_cabecalho

def get_group_mask(weekdays_series):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    mask = ['0'] * 7
    for wd in weekdays_series:
        if wd in days:
            mask[days.index(wd)] = str(days.index(wd) + 1)
    return ''.join(mask)

# ==========================================
# FUNÇÃO PRINCIPAL (CÉREBRO)
# ==========================================
def gerar_ficheiros_rpl(caminho_csv_voos, data_inicio_str, data_fim_str):
    """
    Função otimizada que processa o CSV de malha, cruza com a base de dados e gera o RPL.
    """
    print("A iniciar o processamento do RPL...")

    # 1. LER DA BASE DE DADOS DO SUPABASE
    try:
        from db_utils import get_aeroportos, get_rotas
        
        df_iata_icao = get_aeroportos()
        df_rotas = get_rotas()
        
        if df_iata_icao.empty or df_rotas.empty:
            print("As tabelas de Rotas ou Aeroportos estão vazias. Verifique a importação.")
            return None, None
            
        iata_icao = dict(zip(df_iata_icao['IATA'], df_iata_icao['ICAO']))
            
    except Exception as e:
        print(f"Erro ao ligar ao Supabase: {e}")
        return None, None

    # 2. CONSTRUIR O DICIONÁRIO DE ROTAS (OTIMIZADO - PERFORMANCE)
    routes_map = {}
    for row in df_rotas.to_dict('records'):
        origem, destino = str(row.get('DE', '')).strip(), str(row.get('PARA', '')).strip()
        
        # Mapeamento de velocidade e nível
        mach = str(row.get('MACH', '')).strip()[:5].ljust(5) if pd.notnull(row.get('MACH')) else 'N0000'
        fl_raw = str(row.get('FL', '000')).strip()
        if fl_raw.startswith('F'): fl_raw = fl_raw[1:]
        fl = fl_raw[:3].zfill(3)
            
        rota = str(row.get('ROTA', 'ROUTE UNKNOWN')).strip() if pd.notnull(row.get('ROTA')) else 'ROUTE UNKNOWN'
        route_string = f"{mach} {fl} {rota}"
        
        try: tv_str = str(int(float(row.get('TV', 0)))).zfill(4)
        except: tv_str = "0000"
            
        obs1, obs2 = parse_rmk(row.get('EET'))
        h_inicio, h_fim = parse_time_to_int(row.get('HORA INICIO')), parse_time_to_int(row.get('HORA FIM'))
        
        if (origem, destino) not in routes_map:
            routes_map[(origem, destino)] = {
                'default': {'route': DEFAULT_ROUTE, 'tv': '0000', 'obs1': DEFAULT_RMK_1, 'obs2': DEFAULT_RMK_2}, 
                'timed': []
            }
            
        route_data = {'route': route_string, 'tv': tv_str, 'obs1': obs1, 'obs2': obs2}
        if h_inicio is not None and h_fim is not None:
            routes_map[(origem, destino)]['timed'].append({**route_data, 'start': h_inicio, 'end': h_fim})
        else:
            routes_map[(origem, destino)]['default'] = route_data

    def get_route(origem, destino, dept_time_str):
        pair_routes = routes_map.get((origem, destino))
        if not pair_routes: 
            return {'route': DEFAULT_ROUTE, 'tv': "0000", 'obs1': DEFAULT_RMK_1, 'obs2': DEFAULT_RMK_2}
        
        d_time = parse_time_to_int(dept_time_str)
        if d_time is not None:
            for t_route in pair_routes['timed']:
                s, e = t_route['start'], t_route['end']
                if (s <= e and s <= d_time <= e) or (s > e and (d_time >= s or d_time <= e)): return t_route
        return pair_routes['default']

    # 3. LER O FICHEIRO DE VOOS E APLICAR FILTROS (VETORIZADO)
    try:
        df_voos = pd.read_csv(caminho_csv_voos, sep=';')
    except Exception as e:
        print(f"Erro ao ler o ficheiro CSV: {e}")
        return None, None

    df_voos['Data_Voo'] = pd.to_datetime(df_voos['Day'], format='%d%b%Y')
    data_inicio, data_fim = pd.to_datetime(data_inicio_str), pd.to_datetime(data_fim_str)
    
    df_teste = df_voos[(df_voos['Data_Voo'] >= data_inicio) & (df_voos['Data_Voo'] <= data_fim)].copy()

    if df_teste.empty:
        print("Nenhum voo encontrado no período.")
        return None, None

    # Mapeamentos IATA/ICAO
    df_teste['Dept_Sta_Map'] = df_teste['Dept Sta'].map(iata_icao).fillna(df_teste['Dept Sta'])
    df_teste['Arvl_Sta_Map'] = df_teste['Arvl Sta'].map(iata_icao).fillna(df_teste['Arvl Sta'])

    # Filtro RPL vetorizado (Performance)
    df_teste = df_teste[
        df_teste['Dept_Sta_Map'].str.startswith(PREFIXOS_BR, na=False) & 
        df_teste['Arvl_Sta_Map'].str.startswith(PREFIXOS_BR, na=False) &
        (df_teste['Dept_Sta_Map'] != 'SBJP') &
        (df_teste['Arvl_Sta_Map'] != 'SBJP')
    ].copy()

    if df_teste.empty:
        print("Nenhum voo válido para RPL encontrado.")
        return None, None

    df_teste['Equip_Map'] = df_teste['Equip'].apply(map_equipment)
    df_teste['Dept_Time_Map'] = df_teste['Dept Time'].astype(str).str.replace(':', '')
    df_teste['Aln_Map'] = df_teste['Aln'].apply(lambda x: 'GLO' if x == 'G3' else str(x))
    df_teste['Flt_Id_Map'] = df_teste['Aln_Map'] + df_teste['Flt Num'].astype(float).astype(int).astype(str)

    # 4. PROCESSAR QUEBRAS E AGRUPAMENTOS
    df_teste = df_teste.sort_values(by=['Flt_Id_Map', 'Data_Voo'])
    cols_break = ['Flt_Id_Map', 'Equip_Map', 'Dept_Sta_Map', 'Arvl_Sta_Map', 'Dept_Time_Map']
    df_teste['ID_Bloco'] = (df_teste[cols_break] != df_teste[cols_break].shift(1)).any(axis=1).cumsum()

    # 5. GERAR O CONTEÚDO FINAL
    rpl_lines = []
    csv_data = []
    numero_pagina, voos_na_pagina, LIMITE_POR_PAGINA = 1, 0, 60

    rpl_lines.extend(gerar_cabecalho(data_inicio, numero_pagina))

    for block_id, grupo in df_teste.groupby('ID_Bloco'):
        if voos_na_pagina >= LIMITE_POR_PAGINA:
            numero_pagina += 1
            rpl_lines.extend(gerar_cabecalho(data_inicio, numero_pagina))
            voos_na_pagina = 0 
        
        linha_base = grupo.iloc[0]
        valid_from = grupo['Data_Voo'].min().strftime('%d%m%y')
        valid_to = grupo['Data_Voo'].max().strftime('%d%m%y')
        day_mask = get_group_mask(grupo['Weekday'])
        
        flight_id, equip, dept_sta, arvl_sta, dept_time = (
            linha_base['Flt_Id_Map'], linha_base['Equip_Map'], 
            linha_base['Dept_Sta_Map'], linha_base['Arvl_Sta_Map'], 
            linha_base['Dept_Time_Map']
        )
        
        dados_rota = get_route(dept_sta, arvl_sta, dept_time)
        route_raw, tempo_rpl = dados_rota['route'], dados_rota['tv']
        obs1_final, obs2_raw = str(dados_rota['obs1']).strip(), str(dados_rota['obs2']).strip()
        
        obs2_chunks = textwrap.wrap(obs2_raw, width=30) if obs2_raw else []
        speed_fl, route_body = route_raw[:10], route_raw[10:]
        route_chunks = textwrap.wrap(route_body, width=34) if route_body.strip() else ["ROUTE UNKNOWN"]
        route_str_l1 = f"{speed_fl}{route_chunks[0]}".ljust(46)
        
        line1 = f"   {valid_from} {valid_to} {day_mask} {flight_id:7} {equip:6} {dept_sta}{dept_time} {route_str_l1}{arvl_sta}{tempo_rpl} {obs1_final}"
        rpl_lines.append(line1)
        
        num_extra_lines = max(len(route_chunks) - 1, len(obs2_chunks))
        for i in range(1, num_extra_lines + 1):
            r_chunk = route_chunks[i] if i < len(route_chunks) else ""
            o_chunk = obs2_chunks[i-1] if (i - 1) < len(obs2_chunks) else ""
            if o_chunk.strip() or r_chunk.strip():
                extra_line = f"{' ' * 59}{r_chunk}".ljust(104) + o_chunk
                rpl_lines.append(extra_line)

        voos_na_pagina += 1
        csv_data.append({
            'VALIDO_DESDE': valid_from, 'VALIDO_ATE': valid_to, 'DIAS_OP': day_mask, 'IDENT_ANV': flight_id,
            'TIPO_TURB': equip, 'ADEP': dept_sta, 'EOBT': dept_time, 'ROTA': route_raw, 'DEST': arvl_sta,
            'EET': tempo_rpl, 'OBSERVACOES_1': dados_rota['obs1'], 'OBSERVACOES_2': dados_rota['obs2']
        })

    # 6. EXPORTAR OS FICHEIROS
    output_txt, output_csv = "RPL_Final.txt", "RPL_Dados_Consolidados.csv"
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n'.join(rpl_lines) + '\n')

    pd.DataFrame(csv_data).to_csv(output_csv, index=False, sep=';', encoding='utf-8')
    print(f"✅ Processamento concluído: {output_txt} e {output_csv} gerados.")
    return output_txt, output_csv

if __name__ == '__main__':
    gerar_ficheiros_rpl(
        caminho_csv_voos='Flight_List_UTC_25May26.csv', 
        data_inicio_str='2026-05-28', 
        data_fim_str='2026-06-03'
    )
