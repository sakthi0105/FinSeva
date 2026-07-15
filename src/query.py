import oracledb
import sys
sys.path.append('..')
from config.db_config import get_connection

def query_highest_risk(connection):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT t.TXN_ID, c.ACCOUNT_ID, c.HOME_CITY, c.CREDIT_SCORE,
               t.CITY, t.AMOUNT, t.UNUSUAL_HOUR_FLAG,
               t.CITY_MISMATCH_FLAG, t.RISK_SCORE
        FROM FS_FACT_TRANSACTIONS t
        JOIN FS_DIM_CUSTOMER c ON t.CUSTOMER_KEY = c.CUSTOMER_KEY
        ORDER BY t.RISK_SCORE DESC
    """)

    print("=== Highest Risk Transactions ===")
    for row in cursor.fetchall():
        print(row)

def query_risk_by_city(connection):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT CITY, COUNT(*) AS TXN_COUNT, ROUND(AVG(RISK_SCORE),1) AS AVG_RISK
        FROM FS_FACT_TRANSACTIONS
        GROUP BY CITY
        ORDER BY AVG_RISK DESC
    """)

    print("\n=== Risk By City ===")
    for row in cursor.fetchall():
        print(row)

if __name__ == "__main__":
    connection = get_connection()
    query_highest_risk(connection)
    query_risk_by_city(connection)
    connection.close()
    print("\nConnection closed")