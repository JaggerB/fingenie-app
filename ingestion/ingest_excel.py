from __future__ import annotations

import io
from typing import Dict, List, Tuple
import pandas as pd


def _clean_amount(value) -> float:
    if pd.isna(value):
        return float('nan')
    try:
        if isinstance(value, str):
            txt = value.strip()
            # Handle negative amounts in parentheses e.g., (1,234.00)
            neg = False
            if txt.startswith('(') and txt.endswith(')'):
                neg = True
                txt = txt[1:-1]
            cleaned = (
                txt.replace('USD', '')
                   .replace('GBP', '')
                   .replace('$', '')
                   .replace(',', '')
                   .strip()
            )
            num = float(cleaned)
            return -num if neg else num
        return float(value)
    except Exception:
        return float('nan')


def _detect_period_headers(df: pd.DataFrame) -> List[str]:
    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    headers: List[str] = []
    for col in df.columns:
        cstr = str(col).lower()
        if any(m in cstr for m in months):
            headers.append(str(col))
    if not headers:
        # fallback: treat any numeric columns after the first text column as periods
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        num_cols = [c for c in df.columns if c not in text_cols]
        headers = [str(c) for c in num_cols]
    return headers


def normalize_excel(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Normalize a multi-tab Excel workbook into long-form facts and simple text chunks.

    Returns:
        facts_df: columns [Doc, Sheet, Account, Period, Amount]
        chunks: list of {id, text, metadata}
    """
    xls = pd.ExcelFile(io.BytesIO(file_bytes))
    all_facts: List[pd.DataFrame] = []
    chunks: List[Dict] = []

    for sheet_name in xls.sheet_names:
        try:
            sdf = xls.parse(sheet_name)
        except Exception:
            continue

        if sdf.empty:
            continue

        # Heuristic: first text-like column is account/label column
        text_cols = sdf.select_dtypes(include=['object']).columns.tolist()
        if not text_cols:
            # create a label column from index
            sdf['Label'] = [f'Row {i}' for i in range(len(sdf))]
            label_col = 'Label'
        else:
            label_col = text_cols[0]

        period_cols = _detect_period_headers(sdf)
        if not period_cols:
            # no periods, just two-column [label, amount]
            numeric_cols = sdf.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                tmp = pd.DataFrame({
                    'Doc': filename,
                    'Sheet': sheet_name,
                    'Account': sdf[label_col].astype(str),
                    'Period': 'Unknown',
                    'Amount': sdf[numeric_cols[0]].map(_clean_amount)
                })
                all_facts.append(tmp)
        else:
            # melt into long format
            keep_cols = [label_col] + period_cols
            subset = sdf[keep_cols].copy()
            long_df = subset.melt(id_vars=[label_col], var_name='Period', value_name='Amount')
            long_df['Amount'] = long_df['Amount'].map(_clean_amount)
            long_df.dropna(subset=['Amount'], inplace=True)
            long_df = long_df[long_df['Amount'] != 0]
            long_df.rename(columns={label_col: 'Account'}, inplace=True)
            # Normalize text fields
            long_df['Account'] = long_df['Account'].astype(str).str.strip()
            long_df['Period'] = long_df['Period'].astype(str).str.strip()
            long_df.insert(0, 'Doc', filename)
            long_df.insert(1, 'Sheet', sheet_name)
            all_facts.append(long_df[['Doc', 'Sheet', 'Account', 'Period', 'Amount']])

        # Build simple text chunks per account row for retrieval
        try:
            preview = sdf.head(50).fillna('').astype(str)
            for i, row in preview.iterrows():
                account = row.get(label_col, '')
                numeric_parts = []
                for col in period_cols[:6]:  # cap
                    val = row.get(col, '')
                    if val != '' and str(val) != 'nan':
                        numeric_parts.append(f"{col}={val}")
                if not account and not numeric_parts:
                    continue
                text = f"Sheet {sheet_name} | {account} | " + ", ".join(numeric_parts)
                chunks.append({
                    'id': f"{filename}:{sheet_name}:{i}",
                    'text': text,
                    'metadata': {
                        'doc': filename,
                        'sheet': sheet_name,
                        'row': int(i)
                    }
                })
        except Exception:
            pass

    facts_df = pd.concat(all_facts, ignore_index=True) if all_facts else pd.DataFrame(columns=['Doc','Sheet','Account','Period','Amount'])
    return facts_df, chunks


