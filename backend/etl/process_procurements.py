import pandas as pd
import logging
from .loader import load_to_db, engine
from sqlalchemy import text
from .config import EIS_RESULTS_URLS, EIS_OPENINGS_URLS

logger = logging.getLogger(__name__)

def fetch_and_clean_csv(url: str, sep=';') -> pd.DataFrame:
    """Universāla funkcija CSV ielādei ar kļūdu apstrādi"""
    try:
        # Mēģinām ar norādīto atdalītāju
        df = pd.read_csv(url, sep=sep, dtype=str, on_bad_lines='skip', encoding='utf-8')
        
        # Ja ir tikai 1 kolonna, visticamāk atdalītājs ir nepareizs (dažiem gadiem ir , citiem ;)
        if df.shape[1] < 5:
            alt_sep = ',' if sep == ';' else ';'
            df = pd.read_csv(url, sep=alt_sep, dtype=str, on_bad_lines='skip', encoding='utf-8')
        return df
    except Exception as e:
        logger.error(f"Failed to download/parse CSV from {url}: {e}")
        return pd.DataFrame()

def process_procurements_etl():
    """Galvenā funkcija, kas tiek izsaukta no main.py"""
    
    # 1. Iegūstam eksistējošos uzņēmumus validācijai (lai neimportētu datus par nezināmiem uzņēmumiem)
    logger.info("Fetching existing company list for validation...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT regcode FROM companies"))
        existing_regcodes = set(row[0] for row in result)
    
    # 2. TRUNCATE tabulas VIENU REIZI sākumā
    logger.info("Truncating procurement tables before multi-year load...")
    with engine.connect() as conn:
        trans = conn.begin()
        conn.execute(text("TRUNCATE TABLE procurements CASCADE;"))
        conn.execute(text("TRUNCATE TABLE procurement_bids CASCADE;"))
        trans.commit()
    logger.info("Tables truncated. Starting year-by-year append...")

    # 3. Apstrādājam REZULTĀTUS (Uzvarētāji) - Visus gadus
    logger.info("--- Processing Procurement RESULTS (Winners) ---")
    for year, url in EIS_RESULTS_URLS.items():
        logger.info(f"Processing Results Year: {year}")
        process_single_result_file(url, year, existing_regcodes)

    # 4. Apstrādājam ATVĒRŠANAS (Pretendenti) - Visus gadus
    logger.info("--- Processing Procurement BIDS (Openings) ---")
    for year, url in EIS_OPENINGS_URLS.items():
        logger.info(f"Processing Openings Year: {year}")
        process_single_opening_file(url, year, existing_regcodes)



def process_single_result_file(url: str, year: int, valid_regcodes: set):
    df = fetch_and_clean_csv(url)
    if df.empty: return

    # Kolonnu kartēšana (Mapping)
    col_map = {
        'Uzvaretaja_registracijas_numurs': 'winner_regcode',
        'Liguma_dok_noslegsanas_datums': 'contract_date',
        'Liguma_izpilde_lidz': 'contract_end_date',
        'Izbeigsanas_datums': 'termination_date',
        'Pasutitaja_nosaukums': 'authority_name',
        'Iepirkuma_nosaukums': 'subject',
        'Aktuala_liguma_summa': 'amount',
        'Hipersaite_EIS_kura_pieejams_zinojums': 'source_link'
    }
    df = df.rename(columns=col_map)

    # Pārbaude
    if 'winner_regcode' not in df.columns:
        logger.warning(f"Year {year} missing 'winner_regcode'. Columns: {df.columns.tolist()}")
        return

    # Tīrīšana
    df = df.dropna(subset=['winner_regcode'])
    
    # Naudas tīrīšana (100,50 -> 100.50)
    if 'amount' in df.columns:
        df['amount'] = df['amount'].str.replace(',', '.', regex=False).str.replace(r'\s+', '', regex=True)
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    else:
        df['amount'] = 0.0

    # Datuma tīrīšana
    date_cols = ['contract_date', 'contract_end_date', 'termination_date']
    for dc in date_cols:
        if dc in df.columns:
            # Handle potential excel dates or varied formats if needed, but pd.to_datetime is usually robust
            df[dc] = pd.to_datetime(df[dc], errors='coerce').dt.date

    # Reģistrācijas numura tīrīšana
    df['winner_regcode'] = df['winner_regcode'].astype(str).str.strip()
    df['winner_regcode'] = pd.to_numeric(df['winner_regcode'], errors='coerce')
    df = df.dropna(subset=['winner_regcode'])

    # Filtrējam tikai tos, kas ir mūsu DB
    df = df[df['winner_regcode'].isin(valid_regcodes)]

    # Sagatavojam DB ievadei
    df['year'] = year
    target_cols = ['winner_regcode', 'contract_date', 'contract_end_date', 'termination_date', 'authority_name', 'subject', 'amount', 'year', 'source_link']
    
    # Pieliekam trūkstošās kolonnas kā nulles
    for c in target_cols:
        if c not in df.columns: df[c] = None

    load_to_db(df[target_cols], 'procurements', truncate=False)


def process_single_opening_file(url: str, year: int, valid_regcodes: set):
    df = fetch_and_clean_csv(url)
    if df.empty: return

    # Kartēšana Atvēršanas datiem
    # Mums interesē KURŠ (Pretendents) piedalījās KUR (Iepirkums)
    col_map = {
        'Pretendenta_registracijas_numurs': 'bidder_regcode',
        'Pretendenta_nosaukums': 'bidder_name',
        'Iepirkuma_identifikacijas_numurs': 'procurement_id',
        'Iepirkuma_nosaukums': 'procurement_name',
        'Pasutitaja_nosaukums': 'authority_name',
        'Piedavajumu_atversanas_datums': 'opening_date'
    }
    df = df.rename(columns=col_map)

    if 'bidder_regcode' not in df.columns:
        return

    # Tīrīšana
    df['bidder_regcode'] = df['bidder_regcode'].astype(str).str.strip()
    df['bidder_regcode'] = pd.to_numeric(df['bidder_regcode'], errors='coerce')
    df = df.dropna(subset=['bidder_regcode'])

    # Datums
    if 'opening_date' in df.columns:
        df['opening_date'] = pd.to_datetime(df['opening_date'], errors='coerce').dt.date

    # Validācija pret uzņēmumu reģistru
    df = df[df['bidder_regcode'].isin(valid_regcodes)]

    df['source_year'] = year
    target_cols = ['bidder_regcode', 'bidder_name', 'procurement_id', 'procurement_name', 'authority_name', 'opening_date', 'source_year']
    
    for c in target_cols:
        if c not in df.columns: df[c] = None

    load_to_db(df[target_cols], 'procurement_bids', truncate=False)