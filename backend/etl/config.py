# config.py

DATA_URLS = {
    "register": "https://data.gov.lv/dati/dataset/4de9697f-850b-45ec-8bba-61fa09ce932f/resource/25e80bf3-f107-4ab4-89ef-251b5b9374e9/download/register.csv",
    "equity": "https://data.gov.lv/dati/dataset/5565337a-7f82-41f0-8d16-f091078df603/resource/7910fef5-93eb-4d03-acf0-f45465d67414/download/equity_capitals.csv",
    
    # Officers (Valde)
    "officers": "https://data.gov.lv/dati/dataset/096c7a47-33cd-4dc9-a876-2c86e86230fd/resource/e665114a-73c2-4375-9470-55874b4cfa6b/download/officers.csv",
    # Members (Dalībnieki)
    "members": "https://data.gov.lv/dati/dataset/e1162626-e02a-4545-9236-37553609a988/resource/837b451a-4833-4fd1-bfdd-b45b35a994fd/download/members.csv",
    # PLG (UBO)
    "ubo": "https://data.gov.lv/dati/dataset/b7848ab9-7886-4df0-8bc6-70052a8d9e1a/resource/20a9b26d-d056-4dbb-ae18-9ff23c87bdee/download/beneficial_owners.csv",

    # Risks
    "sanctions": "https://data.gov.lv/dati/dataset/526d69b8-4b81-49a9-94a4-9acf3d601f69/resource/fa10a73f-0a10-4ce7-b0f8-f9652d572a10/download/sanctions.csv",
    "liquidations": "https://data.gov.lv/dati/dataset/09047585-e67a-46c6-8ee8-575987efdef0/resource/59e7ec49-f1c6-4410-8ee6-e7737ac5eaee/download/liquidations.csv",
    "prohibitions": "https://data.gov.lv/dati/dataset/c35c2fce-0014-4664-957f-b71c2f56acae/resource/1a077ff6-4c4e-4cfe-b603-b7e40851e8a9/download/suspensions_prohibitions.csv",
    "securing_measures": "https://data.gov.lv/dati/dataset/b4684b24-3dd2-475e-9502-48cc91b00776/resource/a572e7a4-b23d-44b7-93d8-d09fc47729dd/download/securing_measures.csv",

    # Finance
    "financial_statements": "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/27fcc5ec-c63b-4bfd-bb08-01f073a52d04/download/financial_statements.csv",
    "balance_sheets": "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/50ef4f26-f410-4007-b296-22043ca3dc43/download/balance_sheets.csv",
    "income_statements": "https://data.gov.lv/dati/dataset/8d31b878-536a-44aa-a013-8bc6b669d477/resource/d5fd17ef-d32e-40cb-8399-82b780095af0/download/income_statements.csv",
}

# VARIS Adreses
ADDRESS_URLS = {
    "aw_dziv": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/b83be373-f444-4f50-9b98-28741845325e/download/aw_dziv.csv",
    "aw_eka": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/a510737a-18ce-400f-ad4b-04fce5228272/download/aw_eka.csv",
    "aw_pilseta": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/ee02baa4-2bc3-4f77-a6cb-5427a3e9befe/download/aw_pilseta.csv",
    "aw_novads": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/c62c60bb-58d4-4f26-82c0-5b630769f9d1/download/aw_novads.csv",
    "aw_pagasts": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/6ba8c905-27a1-443a-b9c6-256a0777425b/download/aw_pagasts.csv",
    "aw_ciems": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/0d3810f4-1ac0-4fba-8b10-0188084a361b/download/aw_ciems.csv",
    "aw_iela": "https://data.gov.lv/dati/dataset/6b06a7e8-dedf-4705-a47b-2a7c51177473/resource/3c4ab802-76cf-433c-9c1c-89215e28d833/download/aw_iela.csv"
}


# Iepirkumu REZULTĀTI (Uzvarētāji)
EIS_RESULTS_URLS = {
    2025: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/79b34e1c-8989-4984-816a-8e8f92b701f3/download/eis_e_iepirkumi_rezultati_2025.csv",
    2024: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/3a02a1a7-0322-4c0d-9700-8af9832f0f91/download/eis_e_iepirkumi_rezultati_2024.csv",
    2023: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/71f88053-97c1-4928-93c3-8d83d714f27f/download/eis_e_iepirkumi_rezultati_2023.csv",
    2022: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/97a7c410-60c0-4d08-b554-4d1abb9092da/download/eis_e_iepirkumi_rezultati_2022.csv",
    2021: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/a1342945-ce4b-480b-abb5-b74d43c41534/download/eis_e_iepirkumi_rezultati_2021.csv",
    2020: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/abf811a3-26e8-48c2-bc86-e9b74ca0b385/download/eis_e_iepirkumi_rezultati_2020.csv",
    2019: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/1d37ba16-4d7b-4c1e-9650-1ee9b6a32666/download/eis_e_iepirkumi_rezultati_2019.csv",
    2018: "https://data.gov.lv/dati/dataset/e909312a-61c9-4cde-a72a-0a09dd75ef43/resource/cecd0be7-c8e0-451a-8314-f1d806db3bc1/download/eis_e_iepirkumi_rezultati_2018.csv"
}

# Iepirkumu ATVĒRŠANA (Pretendenti/Dalībnieki)
EIS_OPENINGS_URLS = {
    2025: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/4540cc38-0f5f-42a9-9749-3896c3da4488/download/eis_e_iepirkumi_atversana_2025.csv",
    2024: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/0bba780e-5ae3-4701-ab16-8f804d5a3e57/download/eis_e_iepirkumi_atversana_2024.csv",
    2023: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/7f4f7e75-8207-4ab1-9470-bcd0112653e9/download/eis_e_iepirkumi_atversana_2023.csv",
    2022: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/4b9317d7-8495-4621-966d-48e00639e2cb/download/eis_e_iepirkumi_atversana_2022.csv",
    2021: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/25883190-97ef-45a1-9b89-d15cc418a644/download/eis_e_iepirkumi_atversana_2021.csv",
    2020: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/eb1ddcf9-e358-4ceb-a4d7-e406a0a60d7e/download/eis_e_iepirkumi_atversana_2020.csv",
    2019: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/7f23e4c6-9bee-4552-ba0c-a05be1f6ac62/download/eis_e_iepirkumi_atversana_2019.csv",
    2018: "https://data.gov.lv/dati/dataset/7cfac5a8-8e54-4151-b263-4ca9e51065e9/resource/e40819ee-3a84-4205-b64e-4c67263ac237/download/eis_e_iepirkumi_atversana_2018.csv"
}

# VID Nodokļu Dati
VID_URLS = {
    "tax_payments": "https://data.gov.lv/dati/dataset/5ed74664-b49d-4b28-aacb-040931646e9b/resource/a42d6e8c-1768-4939-ba9b-7700d4f1dd3a/download/pdb_nm_komersantu_samaksato_nodoklu_kopsumas_odata.csv",
    "company_ratings": "https://data.gov.lv/dati/dataset/41481e3e-630f-4b73-b02e-a415d27896db/resource/acd4c6f9-5123-46a5-80f6-1f44b4517f58/download/reitings_uznemumi.csv"
}