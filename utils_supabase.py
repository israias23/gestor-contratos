import os
import bcrypt
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set in environment or .env file')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def register_loja(nome_loja: str, password: str, is_admin: bool=False) -> bool:
    nome_loja = nome_loja.strip()
    if not nome_loja or not password:
        return False
    res = supabase.table('lojas').select('*').eq('nome_loja', nome_loja).execute()
    if res.data and len(res.data) > 0:
        return False
    ph = hash_password(password)
    supabase.table('lojas').insert({'nome_loja': nome_loja, 'senha_hash': ph, 'is_admin': is_admin}).execute()
    return True

def authenticate_loja(nome_loja: str, password: str):
    nome_loja = nome_loja.strip()
    res = supabase.table('lojas').select('*').eq('nome_loja', nome_loja).execute()
    if not res.data or len(res.data) == 0:
        return None
    row = res.data[0]
    ph = row.get('senha_hash') or ''
    if check_password(password, ph):
        return row
    return None

def load_contracts(loja_id: str):
    res = supabase.table('contratos').select('*').eq('loja_id', loja_id).order('data_adicionado', desc=False).execute()
    return res.data or []

def insert_contracts_bulk(loja_id: str, rows: list):
    for r in rows:
        r['loja_id'] = loja_id
    res = supabase.table('contratos').insert(rows).execute()
    return res.data

def upsert_contract(loja_id: str, contrato_key: dict, update_fields: dict):
    q = supabase.table('contratos').select('*').eq('loja_id', loja_id)
    for k,v in contrato_key.items():
        q = q.eq(k, v)
    existing = q.execute()
    if existing.data and len(existing.data) > 0:
        row = existing.data[0]
        supabase.table('contratos').update(update_fields).eq('id', row['id']).execute()
        return 'updated'
    else:
        payload = {'loja_id': loja_id}
        payload.update(contrato_key)
        payload.update(update_fields)
        supabase.table('contratos').insert(payload).execute()
        return 'inserted'

def delete_contract_by_key(loja_id: str, contrato_key: dict):
    q = supabase.table('contratos').delete().eq('loja_id', loja_id)
    for k,v in contrato_key.items():
        q = q.eq(k, v)
    res = q.execute()
    return res.data

def append_audit(loja_id: str, user:str, contrato:str, per:str, mod:str, vencido:str, field:str, old, new):
    supabase.table('audit_log').insert({
        'loja_id': loja_id,
        'user': user,
        'contrato': contrato,
        'per': per,
        'mod': mod,
        'vencido': vencido,
        'field': field,
        'old_value': '' if old is None else str(old),
        'new_value': '' if new is None else str(new)
    }).execute()
