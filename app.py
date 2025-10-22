from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tajny_klic'

app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://student11:spsnet@dbs.spskladno.cz:3306/vyuka11"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users123'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 255 kvůli délce hashů

# Domovská stránka
@app.route('/')
def index():
    return render_template('index.html')

# Přihlášení
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Přihlášení proběhlo úspěšně.", "success")
            return redirect(url_for('index'))
        else:
            error = "Špatné jméno nebo heslo."
    return render_template('login.html', error=error)

# Registrace
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Kontroly
        if not re.fullmatch(r'[A-Za-z0-9_.-]{3,50}', username):
            error = "Uživatelské jméno musí mít 3–50 znaků a musí obsahovat jen písmena, čísla a . _ -"
        elif User.query.filter_by(username=username).first():
            error = "Uživatelské jméno je již obsazeno."
        elif User.query.filter_by(email=email).first():
            error = "Email je již použit."
        elif len(password) < 8:
            error = "Heslo musí mít alespoň 8 znaků."
        elif not re.search(r'[A-Z]', password):
            error = "Heslo musí obsahovat alespoň 1 velké písmeno."
        elif not re.search(r'\d', password):
            error = "Heslo musí obsahovat alespoň 1 číslo."

        if error is None:
            try:
                hashed_password = generate_password_hash(password)
                new_user = User(username=username, email=email, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()  # Tady se zapíše do tabulky users123

                session.clear()
                session['user_id'] = new_user.id
                session['username'] = new_user.username
                flash("Účet byl úspěšně vytvořen.", "success")
                return redirect(url_for('index'))
            except Exception as e:
                db.session.rollback()
                error = "Nastala chyba při vytváření účtu."
    return render_template('register.html', error=error)

# Odhlášení
@app.route('/logout')
def logout():
    session.clear()
    flash("Byl(a) jste odhlášen(a).", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Vytvoří tabulku users123, pokud neexistuje
    with app.app_context():
        db.create_all()
    app.run(debug=True)