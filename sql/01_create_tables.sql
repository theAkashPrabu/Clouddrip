/* =====================================================================
   01_create_tables.sql  |  CloudDrip Gold layer (star schema)
   Run in VS Code mssql extension, connected to clouddrip-db.
   Safe to re-run: it drops old objects first, then rebuilds them.
   ===================================================================== */

-- ---------- 0. Clean slate (drop in reverse order: view -> facts -> dims) ----------
DROP VIEW  IF EXISTS dbo.vw_daily_carbon;
DROP TABLE IF EXISTS dbo.fact_daily_cost;
DROP TABLE IF EXISTS dbo.fact_carbon_intensity;
DROP TABLE IF EXISTS dbo.fact_generation_mix;
DROP TABLE IF EXISTS dbo.dim_resource;
DROP TABLE IF EXISTS dbo.dim_price;
DROP TABLE IF EXISTS dbo.dim_region;
DROP TABLE IF EXISTS dbo.dim_date;
DROP TABLE IF EXISTS dbo.dq_log;
GO

-- ---------- 1. DIMENSIONS (the "menu / calendar / shop list") ----------

-- Calendar: one row per day. date_key like 20261031 makes joins fast.
CREATE TABLE dbo.dim_date (
    date_key      INT          NOT NULL PRIMARY KEY,   -- e.g. 20261031
    full_date     DATE         NOT NULL UNIQUE,
    day_of_month  TINYINT      NOT NULL,
    day_name      NVARCHAR(10) NOT NULL,               -- Monday ...
    is_weekend    BIT          NOT NULL,               -- 1 = Sat/Sun (dev waste!)
    month_num     TINYINT      NOT NULL,
    month_name    NVARCHAR(10) NOT NULL,
    year_num      SMALLINT     NOT NULL
);

-- Regions: all 18 carbon regions; only 2 map to Azure (uksouth, ukwest).
CREATE TABLE dbo.dim_region (
    region_id     TINYINT      NOT NULL PRIMARY KEY,   -- carbon API id (13 = London)
    region_name   NVARCHAR(50) NOT NULL,
    azure_region  NVARCHAR(20) NULL                    -- 'uksouth' / 'ukwest' / NULL
);

-- Price list: one row per service + size + region (from Silver prices).
CREATE TABLE dbo.dim_price (
    price_key       INT IDENTITY(1,1) PRIMARY KEY,     -- auto-numbered id
    service         NVARCHAR(10)  NOT NULL,            -- vm / disk / sql
    sku             NVARCHAR(50)  NOT NULL,            -- e.g. D4s v5, P10, 8 vCore
    azure_region    NVARCHAR(20)  NOT NULL,
    unit            NVARCHAR(30)  NOT NULL,            -- 1 Hour / 1 Month ...
    price_gbp       DECIMAL(12,6) NOT NULL,
    effective_start DATE          NULL,
    CONSTRAINT uq_price UNIQUE (service, sku, azure_region)
);

-- Resources: one row per VM / disk / database in the Harbourline bill.
CREATE TABLE dbo.dim_resource (
    resource_key   INT IDENTITY(1,1) PRIMARY KEY,
    resource_id    NVARCHAR(400) NOT NULL UNIQUE,      -- full Azure ResourceId
    resource_name  NVARCHAR(100) NOT NULL,             -- e.g. hl-web-01
    resource_type  NVARCHAR(100) NULL,
    service_name   NVARCHAR(100) NULL,                 -- Virtual Machines / Storage / SQL
    sku            NVARCHAR(50)  NULL,                 -- links to dim_price.sku
    environment    NVARCHAR(20)  NULL,                 -- prod / dev
    team           NVARCHAR(50)  NULL,
    region_id      TINYINT       NOT NULL
        CONSTRAINT fk_resource_region REFERENCES dbo.dim_region(region_id)
);
GO

-- ---------- 2. FACTS (the "till receipts") ----------

-- Cost: grain = one resource, one day (decision 1A).
CREATE TABLE dbo.fact_daily_cost (
    cost_row_id        INT IDENTITY(1,1) PRIMARY KEY,
    date_key           INT  NOT NULL
        CONSTRAINT fk_cost_date REFERENCES dbo.dim_date(date_key),
    resource_key       INT  NOT NULL
        CONSTRAINT fk_cost_resource REFERENCES dbo.dim_resource(resource_key),
    consumed_quantity  DECIMAL(18,4) NULL,             -- hours used that day
    consumed_unit      NVARCHAR(30)  NULL,
    billed_cost_gbp    DECIMAL(18,4) NOT NULL,
    effective_cost_gbp DECIMAL(18,4) NULL,
    avg_cpu_percent    DECIMAL(5,2)  NULL              -- NULL for disks (no CPU)
);
CREATE INDEX ix_cost_date_resource ON dbo.fact_daily_cost (date_key, resource_key);

-- Carbon: grain = one region, one half-hour (decision 2B part 1).
CREATE TABLE dbo.fact_carbon_intensity (
    period_start_utc    DATETIME2(0) NOT NULL,
    period_end_utc      DATETIME2(0) NOT NULL,
    region_id           TINYINT      NOT NULL
        CONSTRAINT fk_carbon_region REFERENCES dbo.dim_region(region_id),
    intensity_g_per_kwh SMALLINT     NULL,
    intensity_index     NVARCHAR(20) NULL,             -- very low ... very high
    CONSTRAINT pk_carbon PRIMARY KEY (period_start_utc, region_id)
);

-- Generation mix: grain = one region, one half-hour, one fuel.
CREATE TABLE dbo.fact_generation_mix (
    period_start_utc DATETIME2(0) NOT NULL,
    region_id        TINYINT      NOT NULL
        CONSTRAINT fk_mix_region REFERENCES dbo.dim_region(region_id),
    fuel             NVARCHAR(20) NOT NULL,            -- wind, gas, nuclear ...
    percent_share    DECIMAL(5,2) NOT NULL,
    CONSTRAINT pk_mix PRIMARY KEY (period_start_utc, region_id, fuel)
);
GO

-- ---------- 3. DATA QUALITY LOG (Phase 7 writes results here) ----------
CREATE TABLE dbo.dq_log (
    log_id     INT IDENTITY(1,1) PRIMARY KEY,
    run_utc    DATETIME2(0)  NOT NULL DEFAULT SYSUTCDATETIME(),
    table_name NVARCHAR(50)  NOT NULL,
    check_name NVARCHAR(100) NOT NULL,
    expected   NVARCHAR(50)  NULL,
    actual     NVARCHAR(50)  NULL,
    passed     BIT           NOT NULL
);
GO

-- ---------- 4. VIEW: daily carbon average per region (decision 2B part 2) ----------
CREATE VIEW dbo.vw_daily_carbon AS
SELECT
    CAST(c.period_start_utc AS DATE)                    AS carbon_date,
    c.region_id,
    r.region_name,
    r.azure_region,
    AVG(CAST(c.intensity_g_per_kwh AS DECIMAL(8,2)))    AS avg_g_per_kwh,
    MIN(c.intensity_g_per_kwh)                          AS min_g_per_kwh,
    MAX(c.intensity_g_per_kwh)                          AS max_g_per_kwh,
    COUNT(*)                                            AS half_hours
FROM dbo.fact_carbon_intensity AS c
JOIN dbo.dim_region            AS r ON r.region_id = c.region_id
GROUP BY CAST(c.period_start_utc AS DATE), c.region_id, r.region_name, r.azure_region;
GO

-- ---------- 5. Check: list what we built ----------
SELECT TABLE_NAME, TABLE_TYPE
FROM INFORMATION_SCHEMA.TABLES
ORDER BY TABLE_TYPE, TABLE_NAME;