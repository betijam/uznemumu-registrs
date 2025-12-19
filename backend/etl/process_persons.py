import pandas as pd
import logging
from .loader import load_to_db

logger = logging.getLogger(__name__)

def process_persons(officers_path: str, members_path: str, ubo_path: str):
    """
    Apstrādā personas datus no 3 CSV failiem ar paplašinātiem laukiem:
    - Officers: position, rights_of_representation, representation_with_at_least
    - Members: number_of_shares, share_nominal_value, share_currency, legal_entity_regcode
    - UBOs: nationality, residence
    """
    logger.info("Processing Persons with Extended Fields...")
    
    frames = []
    
    # --- 1. Officers (Amatpersonas) ---
    try:
        df_off = pd.read_csv(officers_path, sep=';', dtype=str)
        logger.info(f"Officers CSV columns: {df_off.columns.tolist()[:10]}")
        
        df_off = df_off.rename(columns={
            'at_legal_entity_registration_number': 'company_regcode',
            'name': 'person_name',
            'registered_on': 'date_from',
            'latvian_identity_number_masked': 'person_code',
            'position': 'position',
            'rights_of_representation_type': 'rights_of_representation',
            'representation_with_at_least': 'representation_with_at_least'
        })
        
        df_off['person_name'] = df_off['person_name'].fillna('').str.strip()
        df_off['role'] = 'officer'
        
        # Pārliecinās, ka kolonnas eksistē
        officer_cols = ['company_regcode', 'person_name', 'role', 'person_code', 'date_from',
                        'position', 'rights_of_representation', 'representation_with_at_least']
        for c in officer_cols:
            if c not in df_off.columns:
                df_off[c] = None
        
        df_off['date_to'] = None
        frames.append(df_off[officer_cols + ['date_to']])
        logger.info(f"Processed {len(df_off)} officers")
        
    except Exception as e:
        logger.error(f"Error processing officers: {e}")

    # --- 2. Members (Dalībnieki) ---
    try:
        df_mem = pd.read_csv(members_path, sep=';', dtype=str)
        logger.info(f"Members CSV columns: {df_mem.columns.tolist()[:10]}")
        
        df_mem = df_mem.rename(columns={
            'at_legal_entity_registration_number': 'company_regcode',
            'name': 'person_name',
            'latvian_identity_number_masked': 'person_code',
            'date_from': 'date_from',
            'number_of_shares': 'number_of_shares',
            'share_nominal_value': 'share_nominal_value',
            'share_currency': 'share_currency',
            'legal_entity_registration_number': 'legal_entity_regcode'
        })
        
        df_mem['person_name'] = df_mem['person_name'].fillna('').str.strip()
        df_mem['role'] = 'member'
        
        member_cols = ['company_regcode', 'person_name', 'role', 'person_code', 'date_from',
                       'number_of_shares', 'share_nominal_value', 'share_currency', 'legal_entity_regcode']
        for c in member_cols:
            if c not in df_mem.columns:
                df_mem[c] = None
        
        df_mem['date_to'] = None
        frames.append(df_mem[member_cols + ['date_to']])
        logger.info(f"Processed {len(df_mem)} members")
        
    except Exception as e:
        logger.error(f"Error processing members: {e}")

    # --- 3. UBO (Patiesie Labuma Guvēji) ---
    try:
        df_ubo = pd.read_csv(ubo_path, sep=';', dtype=str)
        logger.info(f"UBO CSV columns: {df_ubo.columns.tolist()[:10]}")
        
        # Apvieno vārdu un uzvārdu
        if 'forename' in df_ubo.columns and 'surname' in df_ubo.columns:
            df_ubo['person_name'] = df_ubo['forename'].fillna('') + ' ' + df_ubo['surname'].fillna('')
        elif 'name' in df_ubo.columns:
            df_ubo['person_name'] = df_ubo['name'].fillna('')
        else:
            df_ubo['person_name'] = ''

        df_ubo = df_ubo.rename(columns={
            'legal_entity_registration_number': 'company_regcode',
            'registered_on': 'date_from',
            'latvian_identity_number_masked': 'person_code',
            'nationality': 'nationality',
            'residence': 'residence'
        })
        
        df_ubo['person_name'] = df_ubo['person_name'].str.strip()
        df_ubo['role'] = 'ubo'
        
        ubo_cols = ['company_regcode', 'person_name', 'role', 'person_code', 'date_from',
                    'nationality', 'residence']
        for c in ubo_cols:
            if c not in df_ubo.columns:
                df_ubo[c] = None

        df_ubo['date_to'] = None
        frames.append(df_ubo[ubo_cols + ['date_to']])
        logger.info(f"Processed {len(df_ubo)} UBOs")
        
    except Exception as e:
        logger.error(f"Error processing UBO: {e}")

    # --- Apvienošana un Tīrīšana ---
    if not frames:
        logger.warning("No person data found.")
        return

    df_final = pd.concat(frames, ignore_index=True)
    
    # Visas mērķa kolonnas
    target_cols = [
        'company_regcode', 'person_name', 'role', 'person_code', 'date_from', 'date_to',
        # Officers
        'position', 'rights_of_representation', 'representation_with_at_least',
        # Members
        'number_of_shares', 'share_nominal_value', 'share_currency', 'legal_entity_regcode',
        # UBOs
        'nationality', 'residence'
    ]
    
    for c in target_cols:
        if c not in df_final.columns:
            df_final[c] = None
    
    df_final = df_final[target_cols]

    # Datu tipu tīrīšana
    df_final['company_regcode'] = pd.to_numeric(df_final['company_regcode'], errors='coerce')
    df_final['person_name'] = df_final['person_name'].replace('', pd.NA)
    df_final = df_final.dropna(subset=['company_regcode', 'person_name'])
    
    # Skaitļu kolonnas
    df_final['representation_with_at_least'] = pd.to_numeric(df_final['representation_with_at_least'], errors='coerce')
    df_final['number_of_shares'] = pd.to_numeric(df_final['number_of_shares'], errors='coerce')
    df_final['share_nominal_value'] = pd.to_numeric(df_final['share_nominal_value'], errors='coerce')
    df_final['legal_entity_regcode'] = pd.to_numeric(df_final['legal_entity_regcode'], errors='coerce')
    
    # Datumu kolonnas
    for d_col in ['date_from', 'date_to']:
        df_final[d_col] = pd.to_datetime(df_final[d_col], errors='coerce').dt.date

    # Dublikātu noņemšana
    initial_count = len(df_final)
    df_final = df_final.drop_duplicates(
        subset=['company_regcode', 'person_name', 'role', 'person_code'], 
        keep='first'
    )
    deduped_count = len(df_final)
    
    if initial_count != deduped_count:
        logger.info(f"Removed {initial_count - deduped_count} duplicate entries.")

    logger.info(f"Loading {len(df_final)} persons to database...")
    load_to_db(df_final, 'persons')
    logger.info("Persons processing complete.")