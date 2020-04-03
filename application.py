from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from tempfile import mkdtemp
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, eur
from ynab import get_assets, get_assets_transactions

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Custom filter
app.jinja_env.filters["eur"] = eur
registering = False


@app.route('/')
@login_required
def index():
    # There is no index page yet
    return redirect('/ynab')


@app.route('/ynab')
@login_required
def ynab():

    conn = sqlite3.connect('ynab.sqlite')
    cur = conn.cursor()

    cur.execute('''SELECT id, date, memo, asset_id, type, amount FROM Transactions WHERE deleted = 0 ORDER BY id desc''')
    transactions = cur.fetchall()
    conn.close()

    return render_template('ynab.html', transactions=transactions)


@app.route('/ynab_assets')
@login_required
def ynab_assets():
    
    conn = sqlite3.connect('ynab.sqlite')
    cur = conn.cursor()

    cur.execute('''SELECT 
	        a.id, a.name,
	        sum(CASE WHEN tr.type = "new" THEN tr.amount ELSE 0 END) start_value,
	        sum(CASE WHEN tr.type = "depreciation" THEN tr.amount ELSE 0 END) depreciation,
	        sum(CASE WHEN tr.type = "sold" THEN tr.amount ELSE 0 END) sold,
	        sum(CASE WHEN tr.type = "new" THEN tr.amount ELSE 0 END) + sum(CASE WHEN tr.type = "depreciation" THEN tr.amount ELSE 0 END) + sum(CASE WHEN tr.type = "sold" THEN tr.amount ELSE 0 END) current_value
        FROM Assets a
        LEFT JOIN Transactions tr ON tr.asset_id = a.id WHERE tr.deleted = 0''')
    assets = cur.fetchall()
    
    conn.close()

    return render_template('ynab_assets.html')


@app.route('/ynab_assets_add', methods=["GET", "POST"])
@login_required
def ynab_assets_add():

    conn = sqlite3.connect('ynab.sqlite')
    cur = conn.cursor()

    print(request.form.get('name'))

    cur.execute('''INSERT INTO Assets (name) VALUES (?)''', (request.form.get('name'),))
    conn.commit()
    conn.close()

    return redirect('/ynab_assets')


@app.route('/ynab_reload')
@login_required
def ynab_reload():

    # Reload Data
    get_assets()
    get_assets_transactions()

    return redirect('/ynab')




@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Login """

    if request.method == 'POST':

        # Query database for user
        conn = sqlite3.connect('webserver.sqlite')
        cur = conn.cursor()

        cur.execute('''SELECT id, username, hash FROM User WHERE username = (?)
        ''', (request.form.get('username'),))
        user = cur.fetchone()

        # If user not found - redirect
        if user == None:
            return redirect("/")

        # Ensure password is correct
        if not check_password_hash(user[2], request.form.get('password')):
            return redirect("/")

        # Log in the user and remember him
        session['user_id'] = user[0]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    """ Register """

    # If Registering is enabled
    if registering == True:
        if request.method == 'POST':

            # Create hash for a password
            hash = generate_password_hash(request.form.get('password'))

            conn = sqlite3.connect('webserver.sqlite')
            cur = conn.cursor()

            # Insert User in database
            cur.execute('''INSERT INTO User (username, hash)
                VALUES (?,?)''', (request.form.get('username'), hash))

            conn.commit()
            conn.close()

            return redirect("/")

        else:
            return render_template("register.html")
    else:
        return redirect("/")


@app.route("/logout")
def logout():
    """ Logout """

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True, port=8080, host='192.168.1.102')