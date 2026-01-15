
import os
import pandas as pd
import io
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    exit(1)
    
engine = create_engine(DATABASE_URL)

CSV_STM = "backend/data/financial_statements.csv"
CSV_INC = "backend/data/income_statements.csv"

def fix_ugp_priority():
    logger.info("🚀 Sākam UGP datu labošanu...")

    if not os.path.exists(CSV_STM) or not os.path.exists(CSV_INC):
        logger.error(f"Missing CSV files in backend/data/. Need both {CSV_STM} and {CSV_INC}")
        return

    # 1. Ielādējam Metadatus (financial_statements.csv)
    logger.info(f"📖 Lasām {CSV_STM}...")
    df_stm = pd.read_csv(CSV_STM, sep=';', dtype={'legal_entity_registration_number': str, 'id': str})
    
    # Prioritātes loģika: UGP (2) > NULL (1) > UKGP (0)
    def get_priority(st):
        st_str = str(st).upper() if pd.notnull(st) else ""
        if st_str == 'UGP': return 2
        if st_str == 'UKGP': return 0
        return 1
        
    df_stm['sort_priority'] = df_stm['source_type'].apply(get_priority)
    df_stm = df_stm.sort_values(['legal_entity_registration_number', 'year', 'sort_priority'])
    
    # Paturam tikai labāko ierakstu uz katru gadu (Deduplikācija)
    df_stm = df_stm.drop_duplicates(subset=['legal_entity_registration_number', 'year'], keep='last')
    
    # Izmetam tos UKGP, kas palikuši (jo gribam aizstāt ar UGP datiem, nevis paturēt UKGP)
    df_stm = df_stm[df_stm['source_type'] != 'UKGP']
    logger.info(f"✅ Atlasīti {len(df_stm)} derīgi (UGP/NULL) pārskatu metadati.")

    # 2. Ielādējam Skaitļus (income_statements.csv)
    logger.info(f"📖 Lasām {CSV_INC} (tas var prasīt laiku)...")
    # Lasām tikai vajadzīgās kolonas, lai taupītu RAM. 
    # Mums vajag statement_id (sasaistei) un finanšu rādītājus.
    cols_to_use = ['statement_id', 'net_turnover', 'net_income']
    df_inc = pd.read_csv(CSV_INC, sep=';', usecols=cols_to_use, dtype=str)
    
    # 3. Savienojam Metadatus ar Skaitļiem pēc statement_id
    df_merged = df_stm.merge(df_inc, left_on='id', right_on='statement_id')
    logger.info(f"🔗 Savienoti {len(df_merged)} ieraksti starp metadatiem un skaitļiem.")

    # 4. Apstrādājam mērvienības (Rounded to nearest)
    def scale_value(val, rounded):
        try:
            if not val or pd.isna(val) or val == 'nan': return 0
            v = float(str(val).replace(',', '.'))
            if str(rounded).upper() == 'THOUSANDS':
                return int(v * 1000)
            return int(v)
        except Exception as e:
            return 0

    logger.info("⚡ Rēķinām mērvienības un mērogojam skaitļus...")
    df_merged['turnover_scaled'] = df_merged.apply(lambda r: scale_value(r['net_turnover'], r['rounded_to_nearest']), axis=1)
    df_merged['profit_scaled'] = df_merged.apply(lambda r: scale_value(r['net_income'], r['rounded_to_nearest']), axis=1)
    df_merged['employees_int'] = pd.to_numeric(df_merged['employees'], errors='coerce').fillna(0).astype(int)

    # 5. Sagatavojam datus atjaunināšanai
    update_data = df_merged[['legal_entity_registration_number', 'year', 'turnover_scaled', 'profit_scaled', 'employees_int', 'source_type']].copy()
    update_data.columns = ['regcode', 'year', 'turnover', 'profit', 'emp', 'st']
    
    logger.info("🔥 Sākam datu ierakstīšanu datubāzē...")
    
    with engine.begin() as conn:
        # 1. Izveidojam pagaidu tabulu
        conn.execute(text("DROP TABLE IF EXISTS temp_fix_ugp"))
        conn.execute(text("""
            CREATE TABLE temp_fix_ugp (
                regcode BIGINT,
                year INT,
                turnover BIGINT,
                profit BIGINT,
                emp INT,
                st TEXT
            )
        """))
        
        # 2. Ielādējam datus pagaidu tabulā
        # Izmantojam sbuf ātrākai ielādei
        s_buf = io.StringIO()
        update_data.to_csv(s_buf, index=False, header=False, sep='\t')
        s_buf.seek(0)
        
        raw_conn = conn.connection
        cursor = raw_conn.cursor()
        cursor.copy_from(s_buf, 'temp_fix_ugp', sep='\t', null="")
        
        # 3. Masveida UPDATE
        logger.info("⚡ Izpildām UPDATE no pagaidu tabulas...")
        result = conn.execute(text("""
            UPDATE financial_reports f
            SET turnover = t.turnover,
                profit = t.profit,
                employees = t.emp,
                source_type = t.st
            FROM temp_fix_ugp t
            WHERE f.company_regcode = t.regcode 
              AND f.year = t.year
              AND (f.turnover != t.turnover OR f.source_type IS DISTINCT FROM t.st);
        """))
        
        logger.info(f"✨ Gatavs! Pārbaudītas un atjauninātas {result.rowcount} rindas.")
        conn.execute(text("DROP TABLE temp_fix_ugp"))

if __name__ == "__main__":
    fix_ugp_priority()
