-- Synapse dedicated SQL pool: bulk-load the landing-zone CSVs written by
-- scripts/load_to_azure_blob.py into the raw schema. Replace <account> and the load date.
-- Uses the workspace managed identity (grant it "Storage Blob Data Reader" on the account).
-- For Azure SQL Database use BULK INSERT ... WITH (DATA_SOURCE = ...) or an ADF Copy activity instead.

COPY INTO raw.customers       FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/customers/load_date=2026-01-01/customers.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
COPY INTO raw.products        FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/products/load_date=2026-01-01/products.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
COPY INTO raw.orders          FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/orders/load_date=2026-01-01/orders.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
COPY INTO raw.order_items     FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/order_items/load_date=2026-01-01/order_items.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
COPY INTO raw.payments        FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/payments/load_date=2026-01-01/payments.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
COPY INTO raw.marketing_spend FROM 'https://<account>.blob.core.windows.net/raw/kenya_retail/marketing_spend/load_date=2026-01-01/marketing_spend.csv'
WITH (FILE_TYPE = 'CSV', FIRSTROW = 2, FIELDQUOTE = '"', CREDENTIAL = (IDENTITY = 'Managed Identity'));
