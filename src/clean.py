import pandas as pd

def save_rejected(rejected_list):
    """Save all rejected records"""
    if rejected_list:
        rejected_df = pd.DataFrame(rejected_list, columns=['rejected_record', 'rejected_reason'])
        
        rejected_df.to_csv(r'C:\Users\ADMIN\Documents\FinSeva\data\rejected\rejected_records.csv', index=False)
        print(f"\nTotal rejected records: {len(rejected_df)}")
        print(rejected_df['rejected_reason'].value_counts().to_string())
    else:
        print("\nNo records rejected")

def clean_transactions(transactions):
    rejected_list = []
    original_count = len(transactions)

    #1.Replace empty strings with NaN so pandas can detect nulls properly
    transactions = transactions.replace('', pd.NA)

    #2.Drop rows where txn_id is null
    null_txn = transactions[transactions['txn_id'].isna()]
    for _, row in null_txn.iterrows():
        rejected_list.append((f"transactions | {row.to_dict()}", "txn_id is null"))
    transactions = transactions[transactions['txn_id'].notna()]

    #3.Drop rows where account_id is null
    null_acc = transactions[transactions['account_id'].isna()]
    for _, row in null_acc.iterrows():
        rejected_list.append((f"transactions | {row.to_dict()}", "account_id is null"))
    transactions = transactions[transactions['account_id'].notna()]

    #4.Remove duplicate txn_ids (keep first)
    duplicates = transactions[transactions['txn_id'].duplicated(keep='first')]
    for _, row in duplicates.iterrows():
        rejected_list.append((f"transactions | {row.to_dict()}", "duplicate txn_id"))
    transactions = transactions.drop_duplicates(subset='txn_id', keep='first')

    #5.Standardize city names (strip whitespace, title case)
    transactions['city'] = transactions['city'].str.strip().str.title()

    #6.Flag rows where amount is null (keep the row)
    transactions['amount_missing_flag'] = transactions['amount'].isna().astype(int)

    #7.Convert amount to float, drop negative or zero (only where amount exists)
    has_amount = transactions['amount'].notna()
    transactions.loc[has_amount, 'amount'] = transactions.loc[has_amount, 'amount'].astype(float)
    bad_amount = transactions[has_amount & (transactions['amount'] <= 0)]
    for _, row in bad_amount.iterrows():
        rejected_list.append((f"transactions | {row.to_dict()}", "amount is negative or zero"))
    transactions = transactions[~(has_amount & (transactions['amount'] <= 0))]

    #8.Convert timestamp to datetime, drop invalid
    original_timestamps = transactions['timestamp'].copy()
    transactions['timestamp'] = pd.to_datetime(transactions['timestamp'], errors='coerce')
    invalid_ts = transactions[transactions['timestamp'].isna()]
    for _, row in invalid_ts.iterrows():
        rejected_list.append((f"transactions | {row.to_dict()}", "invalid timestamp"))
    transactions = transactions[transactions['timestamp'].notna()]

    #9.Reset index after all cleaning
    transactions = transactions.reset_index(drop=True)

    print(f"Transactions: {original_count} --> {len(transactions)} rows after cleaning")
    print(f"Rejected: {len(rejected_list)} rows")

    return transactions, rejected_list


def clean_customers(customers):
    rejected_list = []
    original_count = len(customers)

    #1.Replace empty strings with NaN
    customers = customers.replace('', pd.NA)

    #2.Drop rows where account_id is null
    null_acc = customers[customers['account_id'].isna()]
    for _, row in null_acc.iterrows():
        rejected_list.append((f"customers | {row.to_dict()}", "account_id is null"))
    customers = customers[customers['account_id'].notna()]

    #3.Remove duplicate account_ids (keep first)
    duplicates = customers[customers['account_id'].duplicated(keep='first')]
    for _, row in duplicates.iterrows():
        rejected_list.append((f"customers | {row.to_dict()}", "duplicate account_id"))
    customers = customers.drop_duplicates(subset='account_id', keep='first')

    #4.Standardize home_city (strip whitespace, title case)
    customers['home_city'] = customers['home_city'].str.strip().str.title()

    #5.Drop rows where credit_score is null
    null_cs = customers[customers['credit_score'].isna()]
    for _, row in null_cs.iterrows():
        rejected_list.append((f"customers | {row.to_dict()}", "credit_score is null"))
    customers = customers[customers['credit_score'].notna()]

    #6.Convert credit_score to int, drop outside 300-900
    customers['credit_score'] = customers['credit_score'].astype(int)
    bad_cs = customers[(customers['credit_score'] < 300) | (customers['credit_score'] > 900)]
    for _, row in bad_cs.iterrows():
        rejected_list.append((f"customers | {row.to_dict()}", f"credit_score {row['credit_score']} outside valid range 300-900"))
    customers = customers[(customers['credit_score'] >= 300) & (customers['credit_score'] <= 900)]

    #7.Reset index after all cleaning
    customers = customers.reset_index(drop=True)

    print(f"Customers: {original_count} --> {len(customers)} rows after cleaning")
    print(f"Rejected: {len(rejected_list)} rows")

    return customers, rejected_list


if __name__ == "__main__":
    transactions = pd.read_csv(r'C:\Users\ADMIN\Documents\FinSeva\data\raw\transactions.csv')
    customers = pd.read_csv(r'C:\Users\ADMIN\Documents\FinSeva\data\raw\customers.csv')

    transactions, txn_rejected = clean_transactions(transactions)
    customers, cust_rejected = clean_customers(customers)

    all_rejected = txn_rejected + cust_rejected
    save_rejected(all_rejected)
