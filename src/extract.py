import pandas as pd

def load_data():
    transactions = pd.read_csv(r'C:\Users\ADMIN\Documents\FinSeva\data\raw\transactions.csv')
    customers = pd.read_csv(r'C:\Users\ADMIN\Documents\FinSeva\data\raw\customers.csv')

    print("=== Transactions ===")
    print(transactions.info())
    print(transactions.isnull().sum())

    print("\n=== Customers ===")
    print(customers.info())
    print(customers.isnull().sum())

    return transactions, customers

if __name__ == "__main__":
    load_data()