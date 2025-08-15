
# Gestor de Contratos — v5 (Supabase)

Este projeto está preparado para rodar conectado ao Supabase (Postgres) — já inclui o arquivo `.env` com as credenciais que você forneceu.
**ATENÇÃO:** por segurança, após confirmar que está tudo funcionando você pode remover `.env` do repositório e configurar variáveis de ambiente no Streamlit Cloud.

## Instalação local (testes)
1. Crie e ative um ambiente virtual.
2. Instale dependências:
   pip install -r requirements.txt
3. Execute:
   streamlit run app.py

## Tabelas adicionais (execute no Supabase SQL Editor se necessário)
-- Audit log table
create table if not exists public.audit_log (
    id uuid primary key default uuid_generate_v4(),
    loja_id uuid references public.lojas(id) on delete cascade,
    "user" text,
    contrato text,
    per text,
    mod text,
    vencido text,
    field text,
    old_value text,
    new_value text,
    created_at timestamp default now()
);

-- Recomenda-se também executar a SQL que criamos anteriormente para lojas e contratos caso ainda não tenha.

## Observações
- O app usa o pacote `supabase-client` para se conectar via API REST. As credenciais estão em `.env`.
- O registro/autenticação usa hashing bcrypt para senhas.
- Audit logs são gravados na tabela `audit_log` (SQL acima).
- Para colocar online (Streamlit Cloud), adicione as variáveis de ambiente `SUPABASE_URL` e `SUPABASE_KEY` nas configurações do app e remova o arquivo `.env`.
