import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# --- DATABASE CONNECTION ---
conn = sqlite3.connect("ecommerce.db")

# --- TABLES TO LOAD --- 
tables = {
    "orders": "orders",
    "customers": "customers",
    "geolocation": "geolocation",
    "order_items": "order_items",
    "order_payments": "order_payments",
    "products": "products",
    "sellers": "sellers",
    "categories": "product_category_name_translation"
}

raw = {}

for name, table in tables.items():
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)

    print(f"\n --- {name.upper()} ---")
    print(df.head())
    print(df.info())
    print(df.describe(include='all'))
    print("Shape: ", df.shape)
    print("Nulls: ", df.isna().sum())
    print("Duplicates: ", df.duplicated().sum())

    # Save a clean copy
    raw[name] = df.copy()


# --- DATE CLEANING ---
date_cols = [
    "order_estimated_delivery_date",
    "order_delivered_customer_date",
    "order_delivered_carrier_date",
    "order_approved_at",
    "order_purchase_timestamp"
]

# Convert date columns in orders
for col in date_cols:
    raw['orders'][col] = pd.to_datetime(raw['orders'][col], errors='coerce')

print("\nOrder status distribution:")
print(raw["orders"]["order_status"].value_counts())

print("Date range:")
print(raw["orders"]["order_purchase_timestamp"].min())
print(raw["orders"]["order_purchase_timestamp"].max())

orders_clean = raw["orders"]
customers_clean = raw["customers"]
geolocation_clean = raw["geolocation"]
items_clean = raw["order_items"]
payments_clean = raw["order_payments"]
products_clean = raw["products"]
sellers_clean = raw["sellers"]
categories_clean = raw["categories"]

# --- ORDER ITEMS AGGREGATION ---

# - Avoid duplicate orders caused by multiple items
# - Revenue = sum of item prices + freight
items_summary = items_clean.groupby('order_id').agg({
    'price': 'sum',
    'freight_value': 'sum'
}).reset_index()

# - Assign one category per order
# - Use first product to avoid duplicates
first_item = (
    items_clean
    .drop_duplicates(subset="order_id")
    .merge(
        products_clean[["product_id", "product_category_name"]],
        on="product_id",
        how="left"
    )
)

# Keep payment_value only for checking
payments_summary = payments_clean.groupby('order_id').agg({
    'payment_value':'sum'
}).reset_index()

# --- MERGE CLEAN MODEL ---
df_clean = (
    orders_clean
    .merge(customers_clean, on="customer_id", how="left")
    .merge(items_summary, on="order_id", how="left")
    .merge(first_item[['order_id','product_category_name']], on="order_id", how="left")
    .merge(categories_clean, on="product_category_name", how="left")
    .merge(payments_summary, on='order_id', how='left')
)

print("\n --- DATA MERGE --- ")
print(df_clean.head())
print(df_clean['order_id'].duplicated().sum())

# --- CHECK OF NEGATIVES DATE ---
print("\nPrices negatives: ",(df_clean['price'] < 0).sum())
print("\nNegatives freight value: ",(df_clean['freight_value'] < 0).sum())

# --- BUSINESS FEATURES ---

# Revenue = price + freight_value
df_clean['revenue'] = df_clean['price'] + df_clean['freight_value']

# Total revenue
total_revenue = df_clean['revenue'].sum()
print("\nTotal revenue: ", total_revenue)

# Top 10 categories by revenue
total_revenue_category = (
    df_clean.groupby('product_category_name')['revenue']
    .sum() 
    .sort_values(ascending=False)
    .head(10)
)
print("\nTop 10 categories by revenue:\n", total_revenue_category)

# Top 10 states by revenue
total_revenue_state = (
    df_clean.groupby('customer_state')['revenue']
    .sum() 
    .sort_values(ascending=False)
    .head(10)
)
print("\nTop 10 states by revenue:\n", total_revenue_state)

# Average delivery time (days)
df_clean['delivery_time'] = (df_clean['order_delivered_customer_date'] - df_clean['order_purchase_timestamp']).dt.days
print("\nAverage delivery time (days): ", df_clean['delivery_time'].mean(skipna=True))

# --- MONTHLY KPIs ---
# Create month column
df_clean['month'] = df_clean['order_purchase_timestamp'].dt.to_period("M")

# Orders per month
orders_per_month = df_clean.groupby('month')['order_id'].nunique()
print("\nOrders per month: ", orders_per_month)

# Monthly revenue
monthly_kpi = (
    df_clean.groupby('month')['revenue']
    .sum()
    .reset_index()
)
print("\nMonthly KPI:\n", monthly_kpi)

# MoM % change
monthly_kpi['MoM'] = monthly_kpi['revenue'].pct_change() * 100
print("\nMonthly MoM:\n", monthly_kpi)

# YoY % change
monthly_kpi['YoY_rolling'] = monthly_kpi['revenue'].pct_change(12) * 100
print("\nMonthly YoY:\n", monthly_kpi)

# --- YEARLY KPIs ---
df_clean['year'] = df_clean["order_purchase_timestamp"].dt.to_period('Y')

yearly_kpi = (
    df_clean.groupby('year')['revenue']
    .sum()
    .reset_index()
    .sort_values('year')
)

# YoY annual
yearly_kpi['YoY'] = yearly_kpi['revenue'].pct_change() * 100
print("\nYearly KPI:\n", yearly_kpi)

# --- ROLLING AVERANGES ---
monthly_kpi['rolling_3m'] = monthly_kpi['revenue'].rolling(3).mean()

print("\nMonthly KPI with 3-month rolling average:")
print(monthly_kpi)

# --- YEAR-OVER-YEAR COMPARISION ---

# Compare same month revenue year-over-year
# Shift 12 rows to compare current month with same month last year
monthly_kpi['revenue_last_year'] = monthly_kpi['revenue'].shift(12)

monthly_kpi['YoY_same_month'] = (
    (monthly_kpi['revenue'] - monthly_kpi['revenue_last_year']) 
    / monthly_kpi['revenue_last_year']
) * 100


# Extract month number for seasonality detection
monthly_kpi['month_num'] = monthly_kpi['month'].dt.month

# Seasonality: average revenue by month across years
seasonality = monthly_kpi.groupby('month_num')['revenue'].mean()

print("\nMonthly KPI with YoY and month number:")
print(monthly_kpi)
print("\nSeasonality (average revenue by month):")
print(seasonality)

# --- RFM ANALYSIS ---
# Recency (R) - days since last purchase
# Frequency (F) - number of purchases
# Monetary (M) - total revenue per customer

# Reference date: most recent purchase in dataset
latest_date = df_clean['order_purchase_timestamp'].max()

# Last purchase per customer
last_purchase = df_clean.groupby('customer_id')['order_purchase_timestamp'].max()

recency = (latest_date - last_purchase).dt.days
frequency = df_clean.groupby('customer_id')['order_id'].nunique()
monetary = df_clean.groupby('customer_id')['revenue'].sum()

# Combine into RFM DataFrame
rfm = pd.DataFrame({
    'customer_id': recency.index,
    'Recency': recency.values,
    'Frequency': frequency.values,
    'Monetary': monetary.values
})

print("\nRFM head:")
print(rfm.head())
print("\nRFM summary:")
print(rfm[['Recency','Frequency','Monetary']].describe())

# --- RFM SCORING ---
# Score Recency
rfm['R_score'] = pd.qcut(
    rfm['Recency'],
    q=3,
    labels=[3, 2, 1]
).astype(int)

# Score Frequency
# Frequency groups: one-time, repeat, and frequent customers
rfm['F_score'] = pd.cut(
    rfm['Frequency'],
    bins=[0, 1, 2, float('inf')],
    labels=[1, 2, 3]
).astype(int)

# Score Monetary
# If there are many equal values, I would apply a ranking using rank(method='first') before using qcut to avoid binning issues
rfm['M_score'] = pd.qcut(
    rfm['Monetary'],
    q=3,
    labels=[1, 2, 3]
).astype(int)

# Combine scores into RFM score
rfm['RFM_score'] = (
    rfm['R_score'].astype(str) +
    rfm['F_score'].astype(str) +
    rfm['M_score'].astype(str)
)

# Segment customers
def rfm_segment(row):
    if row['R_score'] == 3 and row['F_score'] == 3 and row['M_score'] == 3:
        return 'VIP'
    elif row['R_score'] == 3 and row['F_score'] >= 2:
        return 'Loyal'
    elif row['R_score'] == 3 and row['F_score'] == 1:
        return 'New'
    elif row['R_score'] == 1:
        return 'Sleeping'
    else:
        return 'Potential'

rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

print("\nCustomer segments counts:")
print(rfm['Segment'].value_counts())

# Aggregate RFM by segment
rfm_summary = rfm.groupby('Segment').agg({
    'customer_id': 'count',
    'Monetary': 'sum',
    'Frequency': 'mean',
    'Recency': 'mean'
})
print("\nRFM summary by segment:")
print(rfm_summary)

# --- VISUALIZATION
# Monthly revenue bar chart
monthly_revenue = df_clean.groupby('month')['revenue'].sum().reset_index()
monthly_revenue['month'] = monthly_revenue['month'].dt.to_timestamp()

plt.figure(figsize=(10, 5))
plt.bar(monthly_revenue['month'], monthly_revenue['revenue'])
plt.title('Monthly Revenue')
plt.xlabel('Month')
plt.ylabel('Revenue')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Seasonality chart
plt.figure(figsize=(8,4))
plt.bar(seasonality.index, seasonality.values)
plt.title('Revenue Seasonality by Month')
plt.xlabel('Month')
plt.ylabel('Average Revenue')
plt.show()
      
# Revenue by RFM segment
rfm.groupby('Segment')['Monetary'].sum().plot(kind='bar')
plt.title('Revenue by RFM Segment')
plt.ylabel('Revenue')
plt.show()

# Delivery time distribution
plt.hist(df_clean['delivery_time'].dropna(), bins=30)
plt.title('Delivery Time Distribution')
plt.xlabel('Days')
plt.ylabel('Orders')
plt.show()

# --- SAVE CLEAN DATAFRAME TO CSV ---
df_clean.to_csv("ecommerce_clean.csv", index=False)
rfm.to_csv("rfm_customers.csv", index=False)
monthly_kpi.to_csv("monthly_kpi.csv", index=False)
