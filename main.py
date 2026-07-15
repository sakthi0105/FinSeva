from src.extract import load_data
from src.clean import clean_transactions, clean_customers, save_rejected
from src.transform import merge_data, add_risk_flags, build_dimensions, build_fact_table
from src.load import create_tables, load_dimensions, load_fact
from src.query import query_highest_risk, query_risk_by_city
from config.db_config import get_connection

def run_pipeline():
    # Step 1: Extract
    print("\n--- EXTRACTING DATA ---")
    transactions, customers = load_data()

    # Step 2: Clean
    print("\n--- CLEANING DATA ---")
    transactions, txn_rejected = clean_transactions(transactions)
    customers, cust_rejected = clean_customers(customers)

    all_rejected = txn_rejected + cust_rejected
    save_rejected(all_rejected)

    # Step 3-6: Transform
    print("\n--- TRANSFORMING DATA ---")
    merged = merge_data(transactions, customers)
    merged = add_risk_flags(merged)
    dim_date, dim_customer = build_dimensions(merged, customers)
    fact_transactions = build_fact_table(merged, dim_date, dim_customer)

    # Step 7-10: Load into Oracle
    print("\n--- LOADING INTO ORACLE ---")
    connection = get_connection()
    create_tables(connection)
    load_dimensions(connection, dim_date, dim_customer)
    load_fact(connection, fact_transactions)

    # Step 11-12: Query the warehouse
    print("\n--- QUERYING WAREHOUSE ---")
    query_highest_risk(connection)
    query_risk_by_city(connection)

    # Step 13: Close connection
    connection.close()
    print("\nPipeline completed. Connection closed.")

if __name__ == "__main__":
    run_pipeline()