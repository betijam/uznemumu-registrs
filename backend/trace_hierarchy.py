import pandas as pd

# Load all CSV files
print("=== Loading CSV files ===")
aw_dziv = pd.read_csv("temp_addresses/aw_dziv.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_eka = pd.read_csv("temp_addresses/aw_eka.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_iela = pd.read_csv("temp_addresses/aw_iela.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_ciems = pd.read_csv("temp_addresses/aw_ciems.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_pagasts = pd.read_csv("temp_addresses/aw_pagasts.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_pilseta = pd.read_csv("temp_addresses/aw_pilseta.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)
aw_novads = pd.read_csv("temp_addresses/aw_novads.csv", sep=',', encoding='utf-8', dtype=str, low_memory=False)

# Create a unified lookup
all_objects = {}
for df, source in [(aw_dziv, 'DZIV'), (aw_eka, 'EKA'), (aw_iela, 'IELA'), 
                    (aw_ciems, 'CIEMS'), (aw_pagasts, 'PAGASTS'), 
                    (aw_pilseta, 'PILSETA'), (aw_novads, 'NOVADS')]:
    for _, row in df.iterrows():
        key = (row['KODS'], row['TIPS_CD'])
        all_objects[key] = {
            'kods': row['KODS'],
            'tips_cd': row['TIPS_CD'],
            'nosaukums': row.get('NOSAUKUMS', ''),
            'std': row.get('STD', ''),
            'vkur_cd': row.get('VKUR_CD'),
            'vkur_tips': row.get('VKUR_TIPS'),
            'source': source
        }

print(f"Loaded {len(all_objects)} total objects\n")

# Trace the hierarchy for KODS 110001306
start_kods = '110001306'
start_tips = '109'  # Telpu grupa

print(f"=== TRACING HIERARCHY FOR KODS {start_kods} ===\n")

current_kods = start_kods
current_tips = start_tips
level = 0
results = {
    'full_address': None,
    'street': None,
    'village': None,
    'parish': None,
    'city': None,
    'municipality': None
}

type_names = {
    '109': 'Telpu grupa',
    '108': 'Ēka',
    '107': 'Iela',
    '106': 'Ciems',
    '105': 'Pagasts',
    '104': 'Pilsēta',
    '113': 'Novads',
    '101': 'Latvija'
}

while current_kods and current_tips:
    key = (current_kods, current_tips)
    if key not in all_objects:
        print(f"⚠️  Level {level}: KODS {current_kods} / TIPS {current_tips} NOT FOUND")
        break
    
    obj = all_objects[key]
    type_name = type_names.get(current_tips, f'Unknown({current_tips})')
    
    print(f"Level {level}: {type_name}")
    print(f"  KODS: {obj['kods']}")
    print(f"  Nosaukums: {obj['nosaukums']}")
    if obj['std']:
        print(f"  Address: {obj['std'][:80]}")
    print(f"  Parent: {obj['vkur_cd']} / {obj['vkur_tips']}")
    
    # Save the full address from telpu grupa
    if level == 0:
        results['full_address'] = obj['std']
    
    # Capture specific types
    if current_tips == '107':
        results['street'] = obj['nosaukums']
    elif current_tips == '106':
        results['village'] = obj['nosaukums']
    elif current_tips == '105':
        results['parish'] = obj['nosaukums']
    elif current_tips == '104':
        results['city'] = obj['nosaukums']
    elif current_tips == '113':
        results['municipality'] = obj['nosaukums']
    
    # Stop if we reached Latvija
    if current_tips == '101':
        print(f"\n✅ Reached top level (Latvija)\n")
        break
    
    # Move to parent
    if pd.isna(obj['vkur_cd']) or obj['vkur_cd'] == '':
        print(f"\n✅ No more parents\n")
        break
    
    current_kods = obj['vkur_cd']
    current_tips = obj['vkur_tips']
    level += 1
    print()

print("=== FINAL RESULTS ===")
print(f"Full Address: {results['full_address']}")
print(f"Street: {results['street']}")
print(f"Village: {results['village']}")  
print(f"Parish: {results['parish']}")
print(f"City: {results['city']}")
print(f"Municipality: {results['municipality']}")

if results['city'] or results['municipality'] or results['parish']:
    print("\n✅ SUCCESS: We can extract pilsēta/novads/pagasts for this address!")
else:
    print("\n❌ PROBLEM: Could not extract pilsēta/novads/pagasts")
