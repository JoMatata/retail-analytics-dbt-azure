-- Azure SQL Database / Synapse dedicated SQL pool: raw landing tables.
-- Every column is text, mirroring the DuckDB `all_varchar` read: typing happens in dbt staging.
-- NOT executed in CI (needs a live Azure workspace).
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'raw') EXEC('CREATE SCHEMA raw');
GO

CREATE TABLE raw.customers (
    customer_id NVARCHAR(20), first_name NVARCHAR(100), last_name NVARCHAR(100), email NVARCHAR(200),
    phone NVARCHAR(40), county NVARCHAR(60), signup_date NVARCHAR(20), signup_channel NVARCHAR(20),
    marketing_opt_in NVARCHAR(10), updated_at NVARCHAR(30)
);
CREATE TABLE raw.products (
    product_id NVARCHAR(20), product_name NVARCHAR(200), category NVARCHAR(60), list_price NVARCHAR(40),
    unit_cost NVARCHAR(40), is_active NVARCHAR(10), created_at NVARCHAR(20)
);
CREATE TABLE raw.orders (
    order_id NVARCHAR(20), customer_id NVARCHAR(20), order_ts NVARCHAR(30), channel NVARCHAR(20),
    delivery_county NVARCHAR(60), payment_method NVARCHAR(30), promo_code NVARCHAR(40),
    order_status NVARCHAR(20), _loaded_at NVARCHAR(30)
);
CREATE TABLE raw.order_items (
    order_item_id NVARCHAR(20), order_id NVARCHAR(20), product_id NVARCHAR(20), quantity NVARCHAR(10),
    unit_price NVARCHAR(40), discount_amount NVARCHAR(40)
);
CREATE TABLE raw.payments (
    payment_id NVARCHAR(20), order_id NVARCHAR(20), payment_method NVARCHAR(30), amount_kes NVARCHAR(40),
    payment_status NVARCHAR(20), paid_at NVARCHAR(30)
);
CREATE TABLE raw.marketing_spend (
    month NVARCHAR(10), channel NVARCHAR(20), campaign_type NVARCHAR(40), spend_kes NVARCHAR(40)
);
GO
