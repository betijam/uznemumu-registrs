-- Address Dimension Schema (VARIS Integration)

CREATE SCHEMA IF NOT EXISTS stage;
CREATE SCHEMA IF NOT EXISTS core;

-- 1. Staging Tables (raw CSV imports)
-- These match the AW_* CSV columns specified in the requirements.
-- Assuming delimiter ';', encoding usually UTF-8 (or Windows-1257, but we'll handle that in Python).
-- Columns: code; type; registered; updated; end_date; address; name; parent_code; parent_type

-- aw_dziv (Telpu grupas)
DROP TABLE IF EXISTS stage.aw_dziv;
CREATE TABLE stage.aw_dziv (
    objekta_kods text,
    objekta_tips text,
    registrets text, -- using text to avoid date parsing errors during COPY, will cast later or keep as reference
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_eka (Ēkas)
DROP TABLE IF EXISTS stage.aw_eka;
CREATE TABLE stage.aw_eka (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_pilseta
DROP TABLE IF EXISTS stage.aw_pilseta;
CREATE TABLE stage.aw_pilseta (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_novads
DROP TABLE IF EXISTS stage.aw_novads;
CREATE TABLE stage.aw_novads (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_pagasts
DROP TABLE IF EXISTS stage.aw_pagasts;
CREATE TABLE stage.aw_pagasts (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_ciems
DROP TABLE IF EXISTS stage.aw_ciems;
CREATE TABLE stage.aw_ciems (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);

-- aw_iela
DROP TABLE IF EXISTS stage.aw_iela;
CREATE TABLE stage.aw_iela (
    objekta_kods text,
    objekta_tips text,
    registrets text,
    aktualizets text,
    beigu_datums text,
    adrese text,
    nosaukums text,
    augst_objekta_kods text,
    augst_objekta_tips text
);


-- 2. Core Address Objects (Unified)
DROP TABLE IF EXISTS core.address_objects CASCADE;
CREATE TABLE core.address_objects (
    kods text PRIMARY KEY,
    tips_cd text,
    std text,
    nosaukums text,
    vkur_cd text,
    vkur_tips text,
    source text
);

CREATE INDEX idx_core_address_objects_vkur ON core.address_objects(vkur_cd, vkur_tips);


-- 3. Core Address Types (Mapping)
-- Codes from Specification 1. Attachment
DROP TABLE IF EXISTS core.address_types;
CREATE TABLE core.address_types (
    tips_cd text PRIMARY KEY,
    type_name text,
    type_group text -- Our logical grouping: 'street', 'village', 'parish', 'city', 'municipality', 'building', 'unit'
);

INSERT INTO core.address_types (tips_cd, type_name, type_group) VALUES
('109', 'Telpu grupa', 'unit'),
('108', 'Ēka', 'building'),
('107', 'Iela', 'street'),
('106', 'Ciems', 'village'),
('110', 'Pagasts', 'parish'),
('104', 'Pilsēta', 'city'),
('113', 'Novads', 'municipality'); 
-- Note: There might be more codes, but these are the main ones requested.


-- 4. Address Dimension Table
DROP TABLE IF EXISTS public.address_dimension CASCADE;
CREATE TABLE public.address_dimension (
    address_id text PRIMARY KEY,
    full_address text,
    street_code text,
    street_name text,
    village_code text,
    village_name text,
    parish_code text,
    parish_name text,
    city_code text,
    city_name text,
    municipality_code text,
    municipality_name text
);

CREATE INDEX idx_address_dimension_city ON public.address_dimension(city_name);
CREATE INDEX idx_address_dimension_muni ON public.address_dimension(municipality_name);
CREATE INDEX idx_address_dimension_parish ON public.address_dimension(parish_name);


-- 5. Helper Function to Refresh Data
CREATE OR REPLACE PROCEDURE core.refresh_address_dimension()
LANGUAGE plpgsql
AS $$
BEGIN
    -- Populate core.address_objects
    TRUNCATE core.address_objects;
    INSERT INTO core.address_objects (kods, tips_cd, std, nosaukums, vkur_cd, vkur_tips, source)
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'DZIV' 
    FROM stage.aw_dziv WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'EKA' 
    FROM stage.aw_eka WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'IELA' 
    FROM stage.aw_iela WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'CIEMS' 
    FROM stage.aw_ciems WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'PAGASTS' 
    FROM stage.aw_pagasts WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'PILSETA' 
    FROM stage.aw_pilseta WHERE objekta_kods IS NOT NULL
    UNION ALL
    SELECT objekta_kods, objekta_tips, adrese, nosaukums, augst_objekta_kods, augst_objekta_tips, 'NOVADS' 
    FROM stage.aw_novads WHERE objekta_kods IS NOT NULL;

    -- Calculate Hierarchy using CTE
    -- Start from ANY object type that might be in companies.addressid
    -- (telpu grupa, ēka, pilsēta, novads, pagasts)
    CREATE TEMP TABLE tmp_hierarchy AS
    WITH RECURSIVE hierarchy AS (
        -- Anchor: Start from ALL object types (not just telpu grupa)
        -- Companies can have addressid pointing to any level
        SELECT
            d.kods               AS leaf_address_id,
            d.kods               AS current_kods,
            d.tips_cd            AS current_tips,
            d.std                AS leaf_full_address,
            d.vkur_cd            AS parent_kods,
            d.vkur_tips          AS parent_tips,
            0                    AS level
        FROM core.address_objects d
        WHERE d.tips_cd IN ('109', '108', '104', '113', '110', '107', '106')
        -- 109=telpu grupa, 108=ēka, 104=pilsēta, 113=novads, 110=pagasts, 107=iela, 106=ciems

        UNION ALL

        -- Recursive Step: Climb up parent hierarchy
        SELECT
            h.leaf_address_id,
            p.kods               AS current_kods,
            p.tips_cd            AS current_tips,
            h.leaf_full_address,
            p.vkur_cd            AS parent_kods,
            p.vkur_tips          AS parent_tips,
            h.level + 1          AS level
        FROM hierarchy h
        JOIN core.address_objects p
          ON p.kods = h.parent_kods
         AND p.tips_cd = h.parent_tips
        WHERE h.level < 10  -- Safety limit to prevent infinite loops
    )
    SELECT * FROM hierarchy;

    CREATE INDEX ON tmp_hierarchy(leaf_address_id);
    CREATE INDEX ON tmp_hierarchy(current_kods);

    -- Populate Dimension
    TRUNCATE public.address_dimension;
    INSERT INTO public.address_dimension (
        address_id, full_address,
        street_code, street_name,
        village_code, village_name,
        parish_code, parish_name,
        city_code, city_name,
        municipality_code, municipality_name
    )
    SELECT
        h.leaf_address_id,
        MAX(CASE WHEN h.level = 0 THEN h.leaf_full_address END) as full_address,
        
        MAX(CASE WHEN t.type_group = 'street'       THEN h.current_kods END) as street_code,
        MAX(CASE WHEN t.type_group = 'street'       THEN o.nosaukums END)    as street_name,

        MAX(CASE WHEN t.type_group = 'village'      THEN h.current_kods END) as village_code,
        MAX(CASE WHEN t.type_group = 'village'      THEN o.nosaukums END)    as village_name,

        MAX(CASE WHEN t.type_group = 'parish'       THEN h.current_kods END) as parish_code,
        MAX(CASE WHEN t.type_group = 'parish'       THEN o.nosaukums END)    as parish_name,

        MAX(CASE WHEN t.type_group = 'city'         THEN h.current_kods END) as city_code,
        MAX(CASE WHEN t.type_group = 'city'         THEN o.nosaukums END)    as city_name,

        MAX(CASE WHEN t.type_group = 'municipality' THEN h.current_kods END) as municipality_code,
        MAX(CASE WHEN t.type_group = 'municipality' THEN o.nosaukums END)    as municipality_name
    FROM tmp_hierarchy h
    LEFT JOIN core.address_objects o ON o.kods = h.current_kods AND o.tips_cd = h.current_tips
    LEFT JOIN core.address_types t ON t.tips_cd = h.current_tips
    GROUP BY h.leaf_address_id;

    DROP TABLE tmp_hierarchy;
END;
$$;


-- 6. Companies View
CREATE OR REPLACE VIEW public.companies_with_address AS
SELECT
    c.*,
    a.full_address,
    a.street_code,
    a.street_name,
    a.village_code,
    a.village_name,
    a.parish_code,
    a.parish_name,
    a.city_code,
    a.city_name,
    a.municipality_code,
    a.municipality_name
FROM companies c
LEFT JOIN address_dimension a ON c.addressid = a.address_id;
