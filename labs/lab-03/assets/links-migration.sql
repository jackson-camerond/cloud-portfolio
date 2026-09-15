-- ---------------------------------------------------------------------------
-- Lab 03 -- migrate the links table to Azure SQL Database (sqldb-app)
--
-- Run this in the Azure portal Query editor, connected to the DATABASE
-- (sqldb-app), signed in as sqladmin. It does three things:
--   1. Creates a CONTAINED database user `appuser` (least privilege -- the
--      app's login, read/write on this one database and nothing else).
--      Contained = the user lives inside the database, no server login needed;
--      this is the recommended pattern on Azure SQL.
--   2. Recreates the dbo.links schema exactly as it was on vm-db-01.
--   3. Reseeds the demo row.
--
-- HONESTY NOTE (say on camera): a real migration moves the data too --
-- BACPAC export/import or Azure Database Migration Service. This table is one
-- seed row plus demo links, so recreate-and-reseed is the honest, right-sized
-- move here.
--
-- BEFORE PASTING: replace CHANGE_ME_APP_PASSWORD with the app password from
-- the values sheet (same value that goes into the Key Vault secret
-- DbAppPassword). Azure SQL enforces complexity: 8+ chars,
-- upper+lower+digit+symbol. This password appears on screen -- blur in the
-- edit; the whole resource group is torn down after publish anyway.
-- ---------------------------------------------------------------------------

-- 1. Least-privilege contained user (the app never uses sqladmin)
IF USER_ID('appuser') IS NULL
    CREATE USER appuser WITH PASSWORD = 'CHANGE_ME_APP_PASSWORD';
ALTER ROLE db_datareader ADD MEMBER appuser;
ALTER ROLE db_datawriter ADD MEMBER appuser;

-- 2. Same schema as Lab 02's vm-db-01 (identical to cloud-init-db.yaml)
IF OBJECT_ID('dbo.links') IS NULL
    CREATE TABLE dbo.links (
        id INT IDENTITY(1,1) PRIMARY KEY,
        code NVARCHAR(16) NOT NULL UNIQUE,
        target NVARCHAR(2048) NOT NULL,
        hits INT NOT NULL DEFAULT 0,
        created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
    );

-- 3. Seed row (the /azure short link the demo relies on)
IF NOT EXISTS (SELECT 1 FROM dbo.links)
    INSERT INTO dbo.links (code, target)
    VALUES (N'azure', N'https://portal.azure.com');

-- Receipt: both should return rows
SELECT name, type_desc FROM sys.database_principals WHERE name = 'appuser';
SELECT code, target, hits FROM dbo.links;
