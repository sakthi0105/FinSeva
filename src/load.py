import oracledb
import pandas as pd
import sys
sys.path.append('..')
from config.db_config import get_connection

def create_tables(connection):
    cursor = connection.cursor()

    for table in ['FS_FACT_TRANSACTIONS', 'FS_DIM_DATE', 'FS_DIM_CUSTOMER']:
        try:
            cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS PURGE")
        except:
            pass

    cursor.execute("""
        CREATE TABLE FS_DIM_DATE (
            DATE_KEY    NUMBER PRIMARY KEY,
            FULL_DATE   DATE,
            DAY         NUMBER,
            MONTH       NUMBER,
            QUARTER     NUMBER,
            YEAR        NUMBER
        )
    """)

    cursor.execute("""
        CREATE TABLE FS_DIM_CUSTOMER (
            CUSTOMER_KEY    NUMBER PRIMARY KEY,
            ACCOUNT_ID      VARCHAR2(20),
            HOME_CITY       VARCHAR2(50),
            CREDIT_SCORE    NUMBER
        )
    """)

    cursor.execute("""
        CREATE TABLE FS_FACT_TRANSACTIONS (
            TXN_KEY             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            TXN_ID              VARCHAR2(20),
            DATE_KEY            NUMBER          REFERENCES FS_DIM_DATE(DATE_KEY),
            CUSTOMER_KEY        NUMBER          REFERENCES FS_DIM_CUSTOMER(CUSTOMER_KEY),
            CITY                VARCHAR2(50),
            AMOUNT              NUMBER(10,2),
            UNUSUAL_HOUR_FLAG   NUMBER(1),
            CITY_MISMATCH_FLAG  NUMBER(1),
            RISK_SCORE          NUMBER,
            AMOUNT_MISSING_FLAG NUMBER(1)
        )
    """)

    connection.commit()
    print("All tables created successfully")

def load_dimensions(connection, dim_date, dim_customer):
    cursor = connection.cursor()

    # Load DIM_DATE
    date_data = list(dim_date[['date_key', 'full_date', 'day', 'month', 'quarter', 'year']]
                     .itertuples(index=False, name=None))

    cursor.executemany(
        """INSERT INTO FS_DIM_DATE (DATE_KEY, FULL_DATE, DAY, MONTH, QUARTER, YEAR)
           VALUES (:1, :2, :3, :4, :5, :6)""",
        date_data
    )

    # Load DIM_CUSTOMER
    customer_data = list(dim_customer[['customer_key', 'account_id', 'home_city', 'credit_score']]
                         .itertuples(index=False, name=None))

    cursor.executemany(
        """INSERT INTO FS_DIM_CUSTOMER (CUSTOMER_KEY, ACCOUNT_ID, HOME_CITY, CREDIT_SCORE)
           VALUES (:1, :2, :3, :4)""",
        customer_data
    )

    connection.commit()
    print(f"Loaded {len(date_data)} rows into FS_DIM_DATE")
    print(f"Loaded {len(customer_data)} rows into FS_DIM_CUSTOMER")

def load_fact(connection, fact_transactions):
    cursor = connection.cursor()

    data = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in fact_transactions[[
            'TXN_ID', 'DATE_KEY', 'CUSTOMER_KEY', 'CITY', 'AMOUNT',
            'UNUSUAL_HOUR_FLAG', 'CITY_MISMATCH_FLAG', 'RISK_SCORE',
            'AMOUNT_MISSING_FLAG'
        ]].itertuples(index=False, name=None)
    ]

    cursor.executemany(
        """INSERT INTO FS_FACT_TRANSACTIONS
           (TXN_ID, DATE_KEY, CUSTOMER_KEY, CITY, AMOUNT,
            UNUSUAL_HOUR_FLAG, CITY_MISMATCH_FLAG, RISK_SCORE,
            AMOUNT_MISSING_FLAG)
           VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)""",
        data
    )

    connection.commit()
    print(f"Loaded {len(data)} rows into FS_FACT_TRANSACTIONS")

if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from extract import load_data
    from clean import clean_transactions
    from transform import merge_data, add_risk_flags, build_dimensions, build_fact_table

    # Extract and transform
    transactions, customers = load_data()
    transactions, txn_rejected = clean_transactions(transactions)
    merged = merge_data(transactions, customers)
    merged = add_risk_flags(merged)
    dim_date, dim_customer = build_dimensions(merged, customers)
    fact_transactions = build_fact_table(merged, dim_date, dim_customer)

    # Load into Oracle
    connection = get_connection()
    create_tables(connection)
    load_dimensions(connection, dim_date, dim_customer)
    load_fact(connection, fact_transactions)
    connection.close()
    print("Connection closed")