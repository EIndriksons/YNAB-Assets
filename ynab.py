import requests
import sqlite3
import json
import re

# Settings:
url = 'https://api.youneedabudget.com/v1'
headers = {'Authorization' : 'Bearer 6b79cbbb9769d743b083955bfeda7e31863498193af6388dfc3c026bdb40ff11'}
budget = '3beb409d-554c-49f6-8891-7cece6507ff6'
accounts = {
    'assets' : 'b26f4a09-cdab-4754-838e-1aae84403811'
}


""" Get and Cache Asset data"""
def get_assets():

    # Setting database
    conn = sqlite3.connect('ynab.sqlite')
    cur = conn.cursor()

    assets = requests.get(url + '/budgets/' + budget + '/accounts/' + accounts['assets'], headers=headers)
    assets = json.loads(json.dumps(assets.json()))['data']['account']

    # Check if already exists in database for caching purposes
    cur.execute('''SELECT * FROM Accounts WHERE ynab_id = (?)
        ''', (assets['id'],))
    assets_cache = cur.fetchone()

    if assets_cache == None:
        # If does not exist - INSERT
        cur.execute('''INSERT INTO Accounts (ynab_id, name, balance)
            VALUES (?,?,?)''', (assets['id'], assets['name'], round(assets['balance']/1000, 2)))
        conn.commit()
    else:
        # If exists and is different - UPDATE
        cur.execute('''UPDATE Accounts
            SET name = (?), balance = (?) WHERE ynab_id = (?)''', (assets['name'], round(assets['balance']/1000,2), assets['id']))
        conn.commit()

    conn.close()


""" Get and Cache Asset Transaction data"""
def get_assets_transactions():

    # Setting database
    conn = sqlite3.connect('ynab.sqlite')
    cur = conn.cursor()

    transactions = requests.get(url + '/budgets/' + budget + '/accounts/' + accounts['assets'] + '/transactions/', headers=headers)
    transactions = json.loads(json.dumps(transactions.json()))['data']['transactions']

    # Check if already exists in database for caching purposes
    cur.execute('''SELECT * FROM Transactions''')
    transactions_cache = cur.fetchall()

    for transaction in transactions:
        # If exists and is different - UPDATE
        condition = exists(transaction, transactions_cache)
        
        cut_out = re.search('(?=\{)(.*?)(?<=\})', transaction['memo'])

        if cut_out != None:
            asset_id = re.search('(?<=\{)(.*?)(?=\})', transaction['memo']).group(0).split(',')[0]
            asset_type = re.search('(?<=\{)(.*?)(?=\})', transaction['memo']).group(0).split(',')[1]
            memo = transaction['memo'].replace(cut_out.group(0), '')
        else:
            asset_id, asset_type = None, None
            memo = transaction['memo']


        if condition == 'UPDATE':
            cur.execute('''UPDATE Transactions
            SET ynab_acc_id = (?), date = (?), memo = (?), asset_id = (?), type = (?), amount = (?), cleared = (?), deleted = (?), flag_color = (?)
            WHERE ynab_id = (?)''', (transaction['account_id'], transaction['date'], memo, asset_id, asset_type, round(transaction['amount']/1000, 2),
                transaction['cleared'], transaction['deleted'], transaction['flag_color'], transaction['id']))
            conn.commit()

        elif condition == 'INSERT':
            cur.execute('''INSERT INTO Transactions (ynab_id, ynab_acc_id, date, memo, asset_id, type, amount, cleared, deleted, flag_color)
            VALUES (?,?,?,?,?,?,?,?,?,?)''', (transaction['id'], transaction['account_id'], transaction['date'], memo, asset_id, asset_type, round(transaction['amount']/1000, 2),
                transaction['cleared'], transaction['deleted'], transaction['flag_color']))
            conn.commit()

    # Check deleted transactions
    for transaction_cache in transactions_cache:
        found = False

        for transaction in transactions:
            if transaction_cache[1] == transaction['id']:
                found = True

        if found == False:
            # UPDATE as Deleted
            cur.execute('''UPDATE Transactions
            SET deleted = (?) WHERE ynab_id = (?)''', (1, transaction_cache[1]))
            conn.commit()
    
    conn.close()


def exists(transaction, transactions_cache):
    # Check each transaction in our database
    if transactions_cache == []:
        return 'INSERT'
    else:
        for transaction_cache in transactions_cache:
            if transaction_cache[1] == transaction['id']:
                return 'UPDATE'
        return 'INSERT'


if __name__ == '__main__':
    get_assets()
    get_assets_transactions()