# This File is for setting up Sqlite3 database
import sqlite3

conn = sqlite3.connect('webserver.sqlite')
cur = conn.cursor()

# Setup webserver db
cur.executescript('''
CREATE TABLE IF NOT EXISTS User (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    username    TEXT NOT NULL UNIQUE,
    hash        TEXT NOT NULL
)
''')

ynab_conn = sqlite3.connect('ynab.sqlite')
ynab_cur = ynab_conn.cursor()

# Setup YNAB db
ynab_cur.executescript('''
DROP TABLE IF EXISTS Accounts;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Assets;

CREATE TABLE Accounts (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    ynab_id     TEXT NOT NULL UNIQUE,
    name        TEXT,
    balance     REAL
);

CREATE TABLE Transactions (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    ynab_id     TEXT NOT NULL UNIQUE,
    ynab_acc_id TEXT NOT NULL,
    date        TEXT NOT NULL,
    memo        TEXT,
    asset_id    INTEGER,
    type        TEXT,
    amount      REAL,
    cleared     TEXT,
    flag_color  TEXT,
    deleted     INTEGER
);

CREATE TABLE Assets (
    id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name        TEXT
);
''')