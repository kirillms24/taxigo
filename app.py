from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from bot_logic import bot_respond

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taxigo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ======= Модели =======
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user/admin/operator

# ======= Маршруты =======
@app.route('/')
def home():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('home.html', user=user)

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    if User.query.filter_by(email=email).first():
        return "Пользователь уже существует"
    new_user = User(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    session['user_id'] = new_user.id
    return redirect(url_for('profile'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email, password=password).first()
    if not user:
        return "Неверный email или пароль"
    session['user_id'] = user.id
    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/support')
def support():
    return render_template('chat.html')

# ======= API для чата с ботом =======
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    message = data.get("message")
    response = bot_respond(message)
    # Здесь можно сохранить сообщение в базе, если нужно
    return jsonify({"response": response})

# ======= Панель администратора =======
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    if user.role != "admin":
        return "Доступ запрещён"
    return render_template('admin.html', user=user)

# ======= Панель оператора =======
@app.route('/operator')
def operator():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    if user.role != "operator" and user.role != "admin":
        return "Доступ запрещён"
    return render_template('operator.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)

