import re
import pandas as pd

SYSTEM_COLUMNS = ["Contrato", "Per.", "Mod.", "Vencido", "Situação", "Justificativa"]

SITUACOES_PADRAO = [
    "Aguardando cortesia",
    "Em análise",
    "Pendente de documentação",
    "Pendente de aprovação",
    "Concluído",
    "Cancelado"
]

def _coalesce_cols(df: pd.DataFrame, targets, fallback=""):
    for tgt in targets:
        if tgt not in df.columns:
            df[tgt] = fallback
    return df

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    col_map = {}
    for col in df.columns:
        c = str(col).strip().lower()
        if 'contrato' in c and 'sub' not in c:
            col_map[col] = "Contrato"
        elif c in ['per.', 'per'] or 'perí' in c or 'period' in c or c == 'periodo' or c == 'período':
            col_map[col] = "Per."
        elif c.startswith('mod') and 'venc' not in c:
            col_map[col] = "Mod."
        elif 'venc' in c:
            col_map[col] = "Vencido"
        elif 'situa' in c:
            col_map[col] = "Situação"
        elif 'just' in c:
            col_map[col] = "Justificativa"
        elif 'mod. vencido' in c or 'mod vencido' in c:
            col_map[col] = "Vencido"
    df = df.rename(columns=col_map)
    df = _coalesce_cols(df, ["Contrato","Per.","Mod.","Vencido","Situação","Justificativa"], "")
    df = df[["Contrato","Per.","Mod.","Vencido","Situação","Justificativa"]]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df

def parse_pasted_table(text: str) -> pd.DataFrame:
    sep = '\t' if '\t' in text else (';' if ';' in text else ',')
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return pd.DataFrame(columns=SYSTEM_COLUMNS)
    import re as _re
    header_tokens = [t.strip() for t in lines[0].split(sep)]
    looks_like_header = any(_re.search(r'contrato|situa|per\.|perí|period|mod\.|mod|venc', h.lower()) for h in header_tokens)
    if looks_like_header:
        data_lines = lines
    else:
        data_lines = ['Contrato'+sep+'Per.'+sep+'Mod.'+sep+'Vencido'+sep+'Situação'+sep+'Justificativa'] + lines
    from io import StringIO
    df = pd.read_csv(StringIO('\n'.join(data_lines)), sep=sep, dtype=str, keep_default_na=False)
    return normalize_columns(df)
