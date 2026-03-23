# Brazil E-Commerce Analysis 🇧🇷

An end-to-end data analysis and interactive dashboard project built on the **Olist Brazilian E-Commerce** public dataset (~100K orders, 2016–2018).

Dashboard Link ---  https://brazil-ecommerce-analytics-nnyceahlgoupewsagfa6dz.streamlit.app/
---

## Project Structure

```
├── olist_*.csv                        # Raw source datasets (from Kaggle)
├── product_category_name_translation.csv
├── merge_datasets.py                  # Merges 9 raw CSVs → main_dataset.csv
├── clean_dataset.py                   # Cleans → main_dataset_clean.csv
├── main.ipynb                         # Full exploratory data analysis (EDA)
├── dashboard.py                       # Interactive Streamlit dashboard
└── requirements.txt
```

---

## Dataset

Download the raw CSVs from Kaggle:
**[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)**

Place all 9 CSV files in the project root alongside the scripts.

---

## Setup

```bash
pip install -r requirements.txt
```

### 1 — Build the merged dataset
```bash
python merge_datasets.py
```
Produces `main_dataset.csv` (~106K rows, 45 columns).

### 2 — Clean the dataset
```bash
python clean_dataset.py
```
Produces `main_dataset_clean.csv` — the final analysis-ready file.

### 3 — Run the EDA notebook
Open `main.ipynb` in VS Code or Jupyter.

### 4 — Launch the dashboard
```bash
streamlit run dashboard.py
```

---

## What's Inside

### EDA Notebook (`main.ipynb`)
- Dataset overview & data quality summary
- Monthly trends: orders, revenue, items sold
- Order timing: day of week & hour of day patterns
- Top product categories by revenue and volume
- Price & freight distributions
- Payment analysis: types, installments, multi-method orders
- Delivery performance vs. estimated dates
- Review score analysis
- Geographic distribution: customers & sellers by Brazilian state (choropleth maps)
- Seller performance: power law distribution, top sellers
- **Seller churn analysis** (2017→2018): churn rate, revenue at risk, retention breakdown
- Correlation heatmap across key numeric features

### Interactive Dashboard (`dashboard.py`)
All the above analysis presented as a live, filterable Streamlit app with:
- Sidebar filters: date range, order status, customer state, product category, payment type, price range
- KPI cards: total orders, GMV, unique customers, average review score
- Plotly interactive charts throughout
- Domain-specific insight cards after every section

---

## Key Findings

| Metric | Value |
|---|---|
| Total orders | ~100K |
| Total GMV | R$ 13.6M |
| Avg review score | 4.07 / 5 |
| Delivered on time | ~92% |
| Repeat customer rate | ~3% |
| Seller churn (2017→2018) | 38.3% |
| Revenue at risk from churn | R$ 668K (11.5% of 2017 GMV) |
| Top customer state | São Paulo (SP) |
| Peak order hour | 2 PM – 4 PM |

---

## Tech Stack

- **Python** — pandas, numpy
- **Visualization** — matplotlib, seaborn, plotly
- **Dashboard** — Streamlit
- **Data** — Olist Brazilian E-Commerce (Kaggle, CC BY-NC-SA 4.0)
