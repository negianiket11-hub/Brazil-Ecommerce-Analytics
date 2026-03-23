import pandas as pd
import numpy as np

print("Loading main_dataset.csv...")
df = pd.read_csv("main_dataset.csv", dtype={"customer_zip_code_prefix": str,
                                             "seller_zip_code_prefix": str})
print(f"  Raw shape: {df.shape}")

# ── 1. Fix column name typos ───────────────────────────────────────────────────
df = df.rename(columns={
    "product_name_lenght":        "product_name_length",
    "product_description_lenght": "product_description_length",
})

# ── 2. Convert timestamps to datetime ─────────────────────────────────────────
timestamp_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
    "shipping_limit_date",
    "review_creation_date",
    "review_answer_timestamp",
]
for col in timestamp_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# ── 3. Zip codes: zero-pad to 5 digits ────────────────────────────────────────
df["customer_zip_code_prefix"] = df["customer_zip_code_prefix"].str.zfill(5)
df["seller_zip_code_prefix"]   = df["seller_zip_code_prefix"].str.zfill(5)

# ── 4. Title-case city names ──────────────────────────────────────────────────
df["customer_city"] = df["customer_city"].str.strip().str.title()
df["seller_city"]   = df["seller_city"].str.strip().str.title()

# ── 5. product_weight_g = 0 is physically invalid → NaN ──────────────────────
df.loc[df["product_weight_g"] == 0, "product_weight_g"] = np.nan

# ── 6. product_category_name nulls → "unknown" ────────────────────────────────
df["product_category_name"]         = df["product_category_name"].fillna("unknown")
df["product_category_name_english"] = df["product_category_name_english"].fillna("unknown")

# ── 7. review comments: null → empty string (no comment is valid) ─────────────
df["review_comment_title"]   = df["review_comment_title"].fillna("")
df["review_comment_message"] = df["review_comment_message"].fillna("")

# ── 8. Flag delivered orders missing a delivery date ──────────────────────────
df["delivery_date_missing_flag"] = (
    (df["order_status"] == "delivered") &
    df["order_delivered_customer_date"].isnull()
).astype(int)
print(f"  Flagged {df['delivery_date_missing_flag'].sum()} 'delivered' orders with no delivery date")

# ── 9. Flag impossible timestamp sequences ────────────────────────────────────
# carrier shipped BEFORE order was approved (1551 rows - source data noise)
df["timestamp_sequence_flag"] = (
    (df["order_delivered_carrier_date"] < df["order_approved_at"]) |
    (df["order_delivered_customer_date"] < df["order_delivered_carrier_date"])
).astype(int)
print(f"  Flagged {df['timestamp_sequence_flag'].sum()} rows with impossible timestamp sequences")

# ── 10. Lat/lng out of Brazil bounding box → NaN ─────────────────────────────
# Brazil: lat -35 to +6, lng -75 to -33
brazil_lat = (-35, 6)
brazil_lng = (-75, -33)

for lat_col, lng_col in [("customer_lat", "customer_lng"), ("seller_lat", "seller_lng")]:
    bad_lat = df[lat_col].notna() & ((df[lat_col] < brazil_lat[0]) | (df[lat_col] > brazil_lat[1]))
    bad_lng = df[lng_col].notna() & ((df[lng_col] < brazil_lng[0]) | (df[lng_col] > brazil_lng[1]))
    bad = bad_lat | bad_lng
    df.loc[bad, [lat_col, lng_col]] = np.nan
    print(f"  Nulled {bad.sum()} out-of-Brazil coordinates in {lat_col}/{lng_col}")

# ── 11. Convert float columns that should be integers (nullable Int64) ─────────
int_cols = {
    "order_item_id":              "Int64",
    "product_name_length":        "Int64",
    "product_description_length": "Int64",
    "product_photos_qty":         "Int64",
    "payment_installments":       "Int64",
    "payment_methods_count":      "Int64",
    "review_score":               "Int64",
}
for col, dtype in int_cols.items():
    if col in df.columns:
        df[col] = df[col].astype(dtype)

# ── 12. Round lat/lng and financials to sensible precision ────────────────────
for col in ["customer_lat", "customer_lng", "seller_lat", "seller_lng"]:
    df[col] = df[col].round(6)
for col in ["price", "freight_value", "payment_total_value"]:
    df[col] = df[col].round(2)

# ── 13. Reorder flag columns to sit next to order_status ─────────────────────
cols = list(df.columns)
for flag in ["delivery_date_missing_flag", "timestamp_sequence_flag"]:
    cols.remove(flag)
status_idx = cols.index("order_status")
cols.insert(status_idx + 1, "delivery_date_missing_flag")
cols.insert(status_idx + 2, "timestamp_sequence_flag")
df = df[cols]

# ── Final validation report ───────────────────────────────────────────────────
print(f"\nFinal shape: {df.shape}")
print("\nRemaining nulls (legitimate missing data):")
nulls = df.isnull().sum()
print(nulls[nulls > 0].to_string())

out = "main_dataset_clean.csv"
df.to_csv(out, index=False)
print(f"\nSaved -> {out}")
