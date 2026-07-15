import pandas as pd

# Merging Table
def merge_data(transactions, customers):

    merged = transactions.merge(customers, on='account_id', how='left')

    print(f"Merged rows: {len(merged)}")
    print(merged.head())

    return merged

# Risk Flag
def add_risk_flags(merged):
    merged['hour'] = merged['timestamp'].dt.hour

    merged['unusual_hour_flag'] = merged['hour'].apply(lambda h: 1 if (h >= 23 or h < 5) else 0)

    merged['city_mismatch_flag'] = (merged['city'] != merged['home_city']).astype(int)

    merged['risk_score'] = merged['unusual_hour_flag'] + merged['city_mismatch_flag']

    print("Risk flags added:")
    print(merged[['txn_id', 'city', 'home_city', 'hour', 'unusual_hour_flag', 'city_mismatch_flag', 'risk_score']])

    return merged

# Dimension Tables
def build_dimensions(merged, customers):
    # DIM_DATE
    dim_date = pd.DataFrame({'full_date': merged['timestamp'].dt.date.unique()})
    dim_date['full_date'] = pd.to_datetime(dim_date['full_date'])
    dim_date['day'] = dim_date['full_date'].dt.day
    dim_date['month'] = dim_date['full_date'].dt.month
    dim_date['quarter'] = dim_date['full_date'].dt.quarter
    dim_date['year'] = dim_date['full_date'].dt.year
    dim_date['date_key'] = range(1, len(dim_date) + 1)

    # DIM_CUSTOMER
    dim_customer = customers.drop_duplicates().reset_index(drop=True)
    dim_customer['customer_key'] = range(1, len(dim_customer) + 1)

    print(f"DIM_DATE rows: {len(dim_date)}")
    print(dim_date)
    print(f"\nDIM_CUSTOMER rows: {len(dim_customer)}")
    print(dim_customer)

    return dim_date, dim_customer

# Fact Table
def build_fact_table(merged, dim_date, dim_customer):
    # Add date_only column for merging with dim_date
    merged['txn_date_only'] = merged['timestamp'].dt.date
    dim_date['full_date_only'] = dim_date['full_date'].dt.date

    # Attach date_key from dim_date
    merged = merged.merge(
        dim_date[['full_date_only', 'date_key']],
        left_on='txn_date_only',
        right_on='full_date_only',
        how='left'
    )

    # Attach customer_key from dim_customer
    merged = merged.merge(
        dim_customer[['account_id', 'customer_key']],
        on='account_id',
        how='left'
    )

    # Select only the columns the fact table needs
    fact_transactions = merged[[
        'txn_id', 'date_key', 'customer_key', 'city', 'amount',
        'unusual_hour_flag', 'city_mismatch_flag', 'risk_score',
        'amount_missing_flag'
    ]].copy()
    fact_transactions.columns = [
    'TXN_ID', 'DATE_KEY', 'CUSTOMER_KEY', 'CITY', 'AMOUNT',
    'UNUSUAL_HOUR_FLAG', 'CITY_MISMATCH_FLAG', 'RISK_SCORE',
    'AMOUNT_MISSING_FLAG'
    ]

    print(f"\nFACT_TRANSACTIONS rows: {len(fact_transactions)}")
    print(fact_transactions)

    return fact_transactions

if __name__ == "__main__":
    from extract import load_data
    from clean import clean_transactions

    transactions, customers = load_data()
    transactions = clean_transactions(transactions)
    merged = merge_data(transactions, customers)
    merged = add_risk_flags(merged)
    dim_date, dim_customer = build_dimensions(merged, customers)
    fact_transactions = build_fact_table(merged, dim_date, dim_customer)