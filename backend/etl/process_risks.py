import pandas as pd
import logging
from .loader import load_to_db, engine
from sqlalchemy import text

logger = logging.getLogger(__name__)

def calculate_risk_score(risk_type: str) -> int:
    """Calculate risk score based on risk type"""
    scores = {
        'sanction': 100,      # CRITICAL - Cannot do business
        'liquidation': 50,    # HIGH - Business ending
        'suspension': 30,     # MEDIUM - Operations restricted
        'securing_measure': 10 # LOW - Financial obligations
    }
    return scores.get(risk_type, 0)


def process_risks(sanctions_path: str, liquidations_path: str, prohibitions_path: str, securing_path: str):
    logger.info("Processing Enhanced Risk Data...")
    
    frames = []

    # 1. SANCTIONS (Sankcijas) - CRITICAL PRIORITY
    try:
        df = pd.read_csv(sanctions_path, sep=';', dtype=str)
        logger.info(f"Loaded {len(df)} sanction records")
        
        # Filter only legal entities (companies)
        df = df.dropna(subset=['legal_entity_registration_number'])
        
        if not df.empty:
            df = df.rename(columns={
                'legal_entity_registration_number': 'company_regcode',
                'entry_date': 'start_date',
                'program': 'sanction_program',
                'list_text': 'sanction_list_text',
                'legal_base_url': 'legal_base_url'
            })
            
            # Build description
            df['description'] = ('Sankcija: ' + 
                                df['sanction_program'].fillna('Nav norādīts') + 
                                ' | ' + 
                                df['sanction_list_text'].fillna(''))
            
            df['risk_type'] = 'sanction'
            df['active'] = True
            df['risk_score'] = calculate_risk_score('sanction')
            
            # Select columns
            cols = ['company_regcode', 'risk_type', 'description', 'active', 'start_date',
                   'sanction_program', 'sanction_list_text', 'legal_base_url', 'risk_score']
            
            for c in cols:
                if c not in df.columns:
                    df[c] = None
            
            frames.append(df[cols])
            logger.info(f"Processed {len(df)} sanctions")
    except Exception as e:
        logger.error(f"Error processing sanctions: {e}")

    # 2. LIQUIDATIONS (Likvidācijas)
    try:
        df = pd.read_csv(liquidations_path, sep=';', dtype=str)
        logger.info(f"Loaded {len(df)} liquidation records")
        
        if not df.empty:
            df = df.rename(columns={
                'legal_entity_registration_number': 'company_regcode',
                'liquidation_type_text': 'liquidation_type',
                'grounds_for_liquidation': 'liquidation_grounds',
                'date_from': 'start_date'
            })
            
            df['description'] = ('Likvidācija: ' + 
                                df['liquidation_type'].fillna('Nav norādīts') + 
                                ' | Pamatojums: ' + 
                                df['liquidation_grounds'].fillna(''))
            
            df['risk_type'] = 'liquidation'
            df['active'] = True  # Assume active if no end date
            df['risk_score'] = calculate_risk_score('liquidation')
            
            cols = ['company_regcode', 'risk_type', 'description', 'active', 'start_date',
                   'liquidation_type', 'liquidation_grounds', 'risk_score']
            
            for c in cols:
                if c not in df.columns:
                    df[c] = None
            
            frames.append(df[cols])
            logger.info(f"Processed {len(df)} liquidations")
    except Exception as e:
        logger.error(f"Error processing liquidations: {e}")

    # 3. SUSPENSIONS/PROHIBITIONS (Darbības apturēšana/Aizliegumi)
    try:
        df = pd.read_csv(prohibitions_path, sep=';', dtype=str)
        logger.info(f"Loaded {len(df)} suspension records")
        
        if not df.empty:
            df = df.rename(columns={
                'legal_entity_registration_number': 'company_regcode',
                'suspension_code_text': 'suspension_code',
                'ground_for': 'suspension_grounds',
                'date_from': 'start_date'
            })
            
            df['description'] = ('Aizliegums: ' + 
                                df['suspension_code'].fillna('Nav norādīts') + 
                                ' | Pamatojums: ' + 
                                df['suspension_grounds'].fillna(''))
            
            df['risk_type'] = 'suspension'
            df['active'] = True
            df['risk_score'] = calculate_risk_score('suspension')
            
            cols = ['company_regcode', 'risk_type', 'description', 'active', 'start_date',
                   'suspension_code', 'suspension_grounds', 'risk_score']
            
            for c in cols:
                if c not in df.columns:
                    df[c] = None
            
            frames.append(df[cols])
            logger.info(f"Processed {len(df)} suspensions")
    except Exception as e:
        logger.error(f"Error processing suspensions: {e}")

    # 4. SECURING MEASURES (Nodrošinājuma līdzekļi)
    try:
        df = pd.read_csv(securing_path, sep=';', dtype=str)
        logger.info(f"Loaded {len(df)} securing measure records")
        
        if not df.empty:
            df = df.rename(columns={
                'legal_entity_registration_number': 'company_regcode',
                'securing_measure_type_text': 'measure_type',
                'institution_name': 'institution_name',
                'case_number': 'case_number',
                'date_from': 'start_date'
            })
            
            df['description'] = ('Nodrošinājums: ' + 
                                df['measure_type'].fillna('Nav norādīts') + 
                                ' | Iestāde: ' + 
                                df['institution_name'].fillna(''))
            
            df['risk_type'] = 'securing_measure'
            df['active'] = True
            df['risk_score'] = calculate_risk_score('securing_measure')
            
            cols = ['company_regcode', 'risk_type', 'description', 'active', 'start_date',
                   'measure_type', 'institution_name', 'case_number', 'risk_score']
            
            for c in cols:
                if c not in df.columns:
                    df[c] = None
            
            frames.append(df[cols])
            logger.info(f"Processed {len(df)} securing measures")
    except Exception as e:
        logger.error(f"Error processing securing measures: {e}")

    # Combine all risk data
    if frames:
        df_all = pd.concat(frames, ignore_index=True)
        
        # Data cleanup
        df_all['company_regcode'] = pd.to_numeric(df_all['company_regcode'], errors='coerce')
        df_all = df_all.dropna(subset=['company_regcode'])
        
        # Convert dates
        if 'start_date' in df_all.columns:
            df_all['start_date'] = pd.to_datetime(df_all['start_date'], errors='coerce').dt.date
        
        # Validate against existing companies
        logger.info("Validating risks against existing companies...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT regcode FROM companies"))
            existing_regcodes = set(row[0] for row in result)
        
        initial_count = len(df_all)
        df_all = df_all[df_all['company_regcode'].isin(existing_regcodes)]
        filtered = initial_count - len(df_all)
        
        if filtered > 0:
            logger.warning(f"Filtered out {filtered} risk records (non-existent companies)")
        
        logger.info(f"Loading {len(df_all)} total risk records to database")
        logger.info(f"  - Sanctions: {len(df_all[df_all['risk_type']=='sanction'])}")
        logger.info(f"  - Liquidations: {len(df_all[df_all['risk_type']=='liquidation'])}")
        logger.info(f"  - Suspensions: {len(df_all[df_all['risk_type']=='suspension'])}")
        logger.info(f"  - Securing Measures: {len(df_all[df_all['risk_type']=='securing_measure'])}")
        
        load_to_db(df_all, 'risks')
    else:
        logger.warning("No risk data to load")
