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

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'bot', 'operator'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    handled_by_operator = db.Column(db.Boolean, default=False)

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
    if 'user_id' not in session:
        return jsonify({"response": "Сессия не найдена, войдите в систему."})
    user_id = session['user_id']
    data = request.json
    message = data.get("message")

    # Сохраняем сообщение пользователя
    user_msg = Message(user_id=user_id, content=message, sender='user')
    db.session.add(user_msg)
    db.session.commit()

    # Получаем ответ бота и сохраняем его
    response = bot_respond(message, user_id=user_id)
    return jsonify({"response": response})

# ======= API для получения новых сообщений оператора =======
@app.route('/fetch_operator_messages')
def fetch_operator_messages():
    if 'user_id' not in session:
        return jsonify({"messages":[]})
    user_id = session['user_id']
    messages = Message.query.filter_by(user_id=user_id, sender='operator').order_by(Message.timestamp).all()
    result = [{"id": m.id, "content": m.content} for m in messages]
    return jsonify({"messages": result})

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
    if user.role not in ['operator', 'admin']:
        return "Доступ запрещён"

    # Выбираем все сообщения пользователей, которые ещё не обработаны
    messages = Message.query.filter_by(sender='user', handled_by_operator=False).all()
    return render_template('operator.html', user=user, messages=messages)

# ======= API для ответа оператора =======
@app.route('/operator_reply', methods=['POST'])
def operator_reply():
    if 'user_id' not in session:
        return jsonify({"status":"error"})
    user = User.query.get(session['user_id'])
    if user.role not in ['operator', 'admin']:
        return jsonify({"status":"error"})

    data = request.json
    msg_id = data.get('message_id')
    reply = data.get('reply')

    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({"status":"error"})

    # Создаем сообщение от оператора
    operator_msg = Message(user_id=msg.user_id, content=reply, sender='operator', handled_by_operator=True)
    db.session.add(operator_msg)

    # Отмечаем исходное сообщение как обработанное
    msg.handled_by_operator = True
    db.session.commit()

    return jsonify({"status":"ok"})

if __name__ == '__main__':
    app.run(debug=True)
