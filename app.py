
import streamlit as st
import pandas as pd
from io import BytesIO
from utils_supabase import register_loja, authenticate_loja, load_contracts, insert_contracts_bulk, upsert_contract, delete_contract_by_key, append_audit
from utils import parse_pasted_table, SITUACOES_PADRAO, normalize_columns
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Gestor de Contratos - v5", page_icon="🚀", layout="wide")

st.title("Gestor de Contratos — v5 (Supabase)")
st.caption("Banco online com Supabase — multiusuário e pronto para a web.")

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.loja = None

with st.sidebar:
    st.header("Acesso")
    if not st.session_state.auth:
        mode = st.radio("Entrar ou Registrar?", ["Entrar","Registrar"])
        nome = st.text_input("Nome da loja")
        senha = st.text_input("Senha", type='password')
        if st.button("Confirmar"):
            if mode == "Registrar":
                ok = register_loja(nome, senha)
                if ok:
                    st.success("Loja registrada! Faça login.")
                else:
                    st.error("Falha no registro (loja pode já existir).")
            else:
                row = authenticate_loja(nome, senha)
                if row:
                    st.session_state.auth = True
                    st.session_state.loja = row
                    st.success(f'Logado: {row.get("nome_loja")}')
                else:
                    st.error("Credenciais inválidas.")
    else:
        st.success(f'Logado: {st.session_state.loja.get("nome_loja")}')
        if st.button("Sair"):
            st.session_state.auth = False
            st.session_state.loja = None

if not st.session_state.auth:
    st.stop()

loja = st.session_state.loja
loja_id = loja.get('id')

tabs = st.tabs(["Importar/Atualizar","Planilha (editar)","Dashboard","Exportar/Imprimir"])

with tabs[0]:
    st.subheader("Importar")
    pasted = st.text_area("Cole a lista (TAB/;/,)", height=180)
    if st.button("Pré-visualizar"):
        df_preview = parse_pasted_table(pasted)
        st.dataframe(df_preview)
        st.session_state.df_preview = df_preview
    if st.button("Adicionar (bulk)"):
        df_in = st.session_state.get('df_preview')
        if df_in is None or df_in.empty:
            st.warning("Sem dados para adicionar.")
        else:
            df_in = normalize_columns(df_in)
            rows = df_in.to_dict(orient='records')
            insert_contracts_bulk(loja_id, rows)
            st.success("Registros enviados ao banco!")

with tabs[1]:
    st.subheader("Planilha (editar)")
    rows = load_contracts(loja_id)
    if rows:
        df = pd.DataFrame(rows)
        df = normalize_columns(df.rename(columns={'situacao':'Situação','justificativa':'Justificativa'}))
    else:
        df = pd.DataFrame(columns=['Contrato','Per.','Mod.','Vencido','Situação','Justificativa'])
    st.dataframe(df, use_container_width=True, height=400)
    st.markdown("---")
    st.markdown("**Editar justificativa (por chave composta)**")
    contrato = st.text_input("Contrato")
    per = st.text_input("Per.")
    mod = st.text_input("Mod.")
    venc = st.text_input("Vencido")
    nova = st.text_area("Justificativa")
    if st.button("Salvar justificativa"):
        if not contrato:
            st.warning("Informe Contrato")
        else:
            key = {'contrato':contrato,'per':per,'mod':mod,'vencido':venc}
            status = upsert_contract(loja_id, key, {'situacao': None, 'justificativa': nova, 'data_adicionado': datetime.utcnow().isoformat()})
            append_audit(loja_id, loja.get('nome_loja'), contrato, per, mod, venc, 'Justificativa', '', nova)
            st.success("Alterado no banco.")

with tabs[2]:
    st.subheader("Dashboard")
    rows = load_contracts(loja_id)
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['Contrato','Per.','Mod.','Vencido','situacao'])
    if not df.empty:
        df = df.rename(columns={'situacao':'Situação'})
        st.bar_chart(df['Situação'].value_counts())

with tabs[3]:
    st.subheader("Exportar")
    rows = load_contracts(loja_id)
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['Contrato','Per.','Mod.','Vencido','situacao'])
    buf = BytesIO()
    df.to_excel(buf, index=False)
    st.download_button("Baixar Excel", data=buf.getvalue(), file_name=f"contratos_{loja.get('nome_loja')}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
