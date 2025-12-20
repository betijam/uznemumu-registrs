"""
VID Nodokļu Datu Apstrāde
- tax_payments: Samaksāto nodokļu kopsummas
- company_ratings: VID nodokļu maksātāja reitings
"""
import pandas as pd
import logging
from .loader import load_to_db, engine
from .config import VID_URLS
from sqlalchemy import text

logger = logging.getLogger(__name__)


def process_tax_payments():
    """
    Apstrādā VID samaksāto nodokļu datus.
    SVARĪGI: Summas ir tūkstošos EUR - jāreizina ar 1000!
    """
    logger.info("Processing VID Tax Payments...")
    
    try:
        url = VID_URLS["tax_payments"]
        logger.info(f"Downloading tax data from {url[:50]}...")
        
        # VID faili izmanto KOMATU kā atdalītāju
        try:
            df = pd.read_csv(url, sep=',', dtype=str, on_bad_lines='skip')
            if df.shape[1] < 5:
                # Mēģinam ar semikolu ja komats nestrādāja
                df = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        except Exception as e:
            logger.warning(f"First parse failed: {e}, trying semicolon...")
            df = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        
        logger.info(f"Loaded {len(df)} rows with {df.shape[1]} columns. First cols: {df.columns.tolist()[:5]}")
        
        # Kolonnu kartēšana (Mapping)
        col_map = {
            'Registracijas_kods': 'company_regcode',
            'Taksacijas_gads': 'year',
            'Samaksato_VID_administreto_nodoklu_kopsumma_tukst_EUR': 'total_tax_paid',
            'Taja_skaita_IIN': 'labor_tax_iin',
            'Taja_skaita_VSAOI': 'social_tax_vsaoi',
            'Videjais_nodarbinato_personu_skaits_cilv': 'avg_employees',
            'Pamatdarbibas_NACE_kods': 'nace_code'
        }
        
        # Pārdēvējam kolonnas
        df = df.rename(columns=col_map)
        
        # Pārbaudām obligātās kolonnas
        required = ['company_regcode', 'year', 'total_tax_paid']
        for col in required:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}. Available: {df.columns.tolist()}")
                return
        
        # Datu tīrīšana
        df['company_regcode'] = pd.to_numeric(df['company_regcode'], errors='coerce')
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['company_regcode', 'year'])
        
        # SVARĪGI: Noņemam atstarpes no skaitļiem (Eiropas formāts: "3 067.73")
        # CSV var izmantot gan parasto atstarpi, gan NON-BREAKING SPACE (U+00A0)
        # un konvertējam no tūkstošiem uz EUR (*1000)
        for col in ['total_tax_paid', 'labor_tax_iin', 'social_tax_vsaoi']:
            if col in df.columns:
                # Noņemam visus atstarpes veidus (parastā + non-breaking)
                df[col] = df[col].astype(str).str.replace(' ', '', regex=False)
                df[col] = df[col].str.replace('\xa0', '', regex=False)  # NON-BREAKING SPACE
                df[col] = df[col].str.replace('\u00a0', '', regex=False)  # Unicode format
                # Aizvietojam komatu ar punktu (ja ir Latvijas formāts)
                df[col] = df[col].str.replace(',', '.', regex=False)
                # Konvertējam uz skaitli un reizinām ar 1000
                df[col] = pd.to_numeric(df[col], errors='coerce') * 1000
        
        # Darbinieku skaits (decimālskaitlis)
        if 'avg_employees' in df.columns:
            df['avg_employees'] = pd.to_numeric(df['avg_employees'], errors='coerce')
        
        # Validācija pret companies tabulu
        logger.info("Validating against existing companies...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT regcode FROM companies"))
            existing_regcodes = set(row[0] for row in result)
        
        initial_count = len(df)
        df = df[df['company_regcode'].isin(existing_regcodes)]
        filtered = initial_count - len(df)
        if filtered > 0:
            logger.warning(f"Filtered out {filtered} records (non-existent companies)")
        
        # Atlasām galīgās kolonnas
        final_cols = ['company_regcode', 'year', 'total_tax_paid', 'labor_tax_iin', 
                      'social_tax_vsaoi', 'avg_employees', 'nace_code']
        for c in final_cols:
            if c not in df.columns:
                df[c] = None
        
        # Noņemam dublikātus (viņš uzņēmumam gadā viens ieraksts)
        df = df.drop_duplicates(subset=['company_regcode', 'year'], keep='last')
        
        logger.info(f"Loading {len(df)} tax payment records...")
        load_to_db(df[final_cols], 'tax_payments')
        
    except Exception as e:
        logger.error(f"Error processing tax payments: {e}")
        raise


def process_company_ratings():
    """
    Apstrādā VID nodokļu maksātāja reitingu.
    Šī tabula glabā tikai aktuālo reitingu (UPSERT).
    """
    logger.info("Processing VID Company Ratings...")
    
    try:
        url = VID_URLS["company_ratings"]
        logger.info(f"Downloading ratings from {url[:50]}...")
        
        # VID faili izmanto KOMATU kā atdalītāju
        try:
            df = pd.read_csv(url, sep=',', dtype=str, on_bad_lines='skip')
            if df.shape[1] < 3:
                df = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        except Exception as e:
            logger.warning(f"First parse failed: {e}, trying semicolon...")
            df = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
        
        logger.info(f"Loaded {len(df)} rows with {df.shape[1]} columns. First cols: {df.columns.tolist()[:5]}")
        
        # Kolonnu kartēšana
        col_map = {
            'Registracijas_kods': 'company_regcode',
            'Reitings': 'rating_grade',
            'Skaidrojums': 'rating_explanation',
            'Informacijas_atjaunosanas_datums': 'last_evaluated_on'
        }
        
        df = df.rename(columns=col_map)
        
        if 'company_regcode' not in df.columns:
            logger.error(f"Missing regcode column. Available: {df.columns.tolist()}")
            return
        
        # Datu tīrīšana
        df['company_regcode'] = pd.to_numeric(df['company_regcode'], errors='coerce')
        df = df.dropna(subset=['company_regcode'])
        
        # Datuma konversija
        if 'last_evaluated_on' in df.columns:
            df['last_evaluated_on'] = pd.to_datetime(df['last_evaluated_on'], errors='coerce').dt.date
        
        # FK validācija
        logger.info("Validating against existing companies...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT regcode FROM companies"))
            existing_regcodes = set(row[0] for row in result)
        
        initial_count = len(df)
        df = df[df['company_regcode'].isin(existing_regcodes)]
        filtered = initial_count - len(df)
        if filtered > 0:
            logger.warning(f"Filtered out {filtered} ratings (non-existent companies)")
        
        # Galīgās kolonnas
        final_cols = ['company_regcode', 'rating_grade', 'rating_explanation', 'last_evaluated_on']
        for c in final_cols:
            if c not in df.columns:
                df[c] = None
        
        # Viens reitings katram uzņēmumam
        df = df.drop_duplicates(subset=['company_regcode'], keep='last')
        
        logger.info(f"Loading {len(df)} company ratings...")
        load_to_db(df[final_cols], 'company_ratings')
        
    except Exception as e:
        logger.error(f"Error processing company ratings: {e}")
        raise


def process_vid_data():
    """Galvenā funkcija, kas apstrādā visus VID datus + NACE klasifikāciju."""
    logger.info("=== Starting VID Data Processing ===")
    process_tax_payments()
    process_company_ratings()
    
    # Process NACE Classification using VID tax data
    try:
        import os
        from .process_nace import process_nace
        
        nace_path = os.path.join(os.path.dirname(__file__), '..', '..', 'NACE.csv')
        vid_path = os.path.join('/tmp', 'etl_data', 'vid_tax_data.csv')  # Downloaded by process_tax_payments
        
        if os.path.exists(nace_path):
            logger.info("NACE dictionary found, processing industry classification...")
            
            # Re-download VID tax data for NACE processing
            # (Alternative: we could cache it, but re-downloading ensures consistency)
            from .config import VID_URLS
            import pandas as pd
            
            logger.info("Re-downloading VID tax data for NACE processing...")
            url = VID_URLS["tax_payments"]
            
            # Download to temp location
            try:
                df_temp = pd.read_csv(url, sep=',', dtype=str, on_bad_lines='skip')
                if df_temp.shape[1] < 5:
                    df_temp = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
            except:
                df_temp = pd.read_csv(url, sep=';', dtype=str, on_bad_lines='skip')
            
            # Save to temp file
            os.makedirs('/tmp/etl_data', exist_ok=True)
            df_temp.to_csv(vid_path, index=False, sep=';')
            
            # Process NACE
            process_nace(vid_path, nace_path)
        else:
            logger.warning(f"NACE.csv not found at {nace_path}, skipping industry classification")
    
    except Exception as e:
        logger.error(f"Error processing NACE classification: {e}")
        # Don't raise - NACE is optional enhancement
    
    logger.info("=== VID Data Processing Complete ===")

