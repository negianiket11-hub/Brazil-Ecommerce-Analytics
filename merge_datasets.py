import pandas as pd
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# Load all datasets
print("Loading datasets...")
orders       = pd.read_csv(os.path.join(BASE, "olist_orders_dataset.csv"))
customers    = pd.read_csv(os.path.join(BASE, "olist_customers_dataset.csv"))
order_items  = pd.read_csv(os.path.join(BASE, "olist_order_items_dataset.csv"))
payments     = pd.read_csv(os.path.join(BASE, "olist_order_payments_dataset.csv"))
reviews      = pd.read_csv(os.path.join(BASE, "olist_order_reviews_dataset.csv"))
products     = pd.read_csv(os.path.join(BASE, "olist_products_dataset.csv"))
sellers      = pd.read_csv(os.path.join(BASE, "olist_sellers_dataset.csv"))
category_tr  = pd.read_csv(os.path.join(BASE, "product_category_name_translation.csv"))
geolocation  = pd.read_csv(os.path.join(BASE, "olist_geolocation_dataset.csv"))

# ── Geolocation: average lat/lng per zip code prefix ──────────────────────────
geo_avg = (
    geolocation
    .groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]]
    .mean()
    .reset_index()
    .rename(columns={
        "geolocation_zip_code_prefix": "zip_prefix",
        "geolocation_lat": "lat",
        "geolocation_lng": "lng",
    })
)

# ── Payments: aggregate per order ─────────────────────────────────────────────
# Total value, number of installments, dominant payment type
payments_agg = (
    payments
    .groupby("order_id")
    .agg(
        payment_total_value=("payment_value", "sum"),
        payment_installments=("payment_installments", "max"),
        payment_type=("payment_type", lambda x: x.value_counts().index[0]),
        payment_methods_count=("payment_sequential", "max"),
    )
    .reset_index()
)

# ── Reviews: one review per order (highest score if multiple) ─────────────────
reviews_agg = (
    reviews
    .sort_values("review_score", ascending=False)
    .drop_duplicates(subset="order_id", keep="first")
    [["order_id", "review_score", "review_comment_title", "review_comment_message",
      "review_creation_date", "review_answer_timestamp"]]
)

# ── Products: add English category name ───────────────────────────────────────
# Strip BOM from column name if present
category_tr.columns = category_tr.columns.str.lstrip("\ufeff")
products_full = products.merge(category_tr, on="product_category_name", how="left")

# ── Sellers: rename columns to avoid conflicts ─────────────────────────────────
sellers = sellers.rename(columns={
    "seller_zip_code_prefix": "seller_zip_code_prefix",
    "seller_city": "seller_city",
    "seller_state": "seller_state",
})

# ── Build main dataset ─────────────────────────────────────────────────────────
# Grain: one row per order item
print("Merging...")

df = (
    order_items
    # 1. Add order info
    .merge(orders, on="order_id", how="left")
    # 2. Add customer info
    .merge(customers, on="customer_id", how="left")
    # 3. Add product info (with English category)
    .merge(products_full, on="product_id", how="left")
    # 4. Add seller info
    .merge(sellers, on="seller_id", how="left")
    # 5. Add payment aggregates
    .merge(payments_agg, on="order_id", how="left")
    # 6. Add review
    .merge(reviews_agg, on="order_id", how="left")
)

# 7. Add customer geolocation
df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].astype(str).str.zfill(5)
geo_avg["zip_prefix"] = geo_avg["zip_prefix"].astype(str).str.zfill(5)

df = df.merge(
    geo_avg.rename(columns={"zip_prefix": "customer_zip_code_prefix",
                             "lat": "customer_lat", "lng": "customer_lng"}),
    on="customer_zip_code_prefix",
    how="left",
)

# 8. Add seller geolocation
df["seller_zip_code_prefix"] = df["seller_zip_code_prefix"].astype(str).str.zfill(5)
df = df.merge(
    geo_avg.rename(columns={"zip_prefix": "seller_zip_code_prefix",
                             "lat": "seller_lat", "lng": "seller_lng"}),
    on="seller_zip_code_prefix",
    how="left",
)

# ── Reorder columns logically ─────────────────────────────────────────────────
col_order = [
    # Order identifiers
    "order_id", "order_item_id", "order_status",
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date",
    # Customer
    "customer_id", "customer_unique_id",
    "customer_city", "customer_state", "customer_zip_code_prefix",
    "customer_lat", "customer_lng",
    # Product
    "product_id", "product_category_name", "product_category_name_english",
    "product_name_lenght", "product_description_lenght", "product_photos_qty",
    "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm",
    # Seller
    "seller_id", "seller_city", "seller_state", "seller_zip_code_prefix",
    "seller_lat", "seller_lng",
    # Item financials
    "price", "freight_value", "shipping_limit_date",
    # Payment
    "payment_type", "payment_installments", "payment_methods_count", "payment_total_value",
    # Review
    "review_score", "review_comment_title", "review_comment_message",
    "review_creation_date", "review_answer_timestamp",
]

# Only keep columns that exist
col_order = [c for c in col_order if c in df.columns]
df = df[col_order]

out_path = os.path.join(BASE, "main_dataset.csv")
df.to_csv(out_path, index=False)
print(f"Done! Saved {len(df):,} rows x {len(df.columns)} columns -> main_dataset.csv")
print(f"\nColumn list:\n{list(df.columns)}")
