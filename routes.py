from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from db import Aluno, Nota, Usuario, get_boletim, get_stats

# Blueprints
auth_bp = Blueprint('auth', __name__)
dashboard_bp = Blueprint('dashboard', __name__)
alunos_bp = Blueprint('alunos', __name__, url_prefix='/alunos')

# --- AUTH ROUTES ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        user = Usuario.verify(username, senha)
        if user:
            session['user'] = user['username']
            return redirect(url_for('dashboard.index'))
        return render_template('login.html', error="Credenciais inválidas")
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth.login'))

# --- DASHBOARD ROUTES ---
@dashboard_bp.before_request
def check_auth():
    if 'user' not in session and request.endpoint != 'auth.login':
        # Se for uma requisição de API (JSON ou caminhos específicos), retorna 401 em vez de redirecionar
        if request.is_json or request.path.startswith('/stats') or '/alunos/' in request.path:
            return jsonify({"success": False, "message": "Não autorizado"}), 401
        return redirect(url_for('auth.login'))

@dashboard_bp.route('/')
def index():
    return render_template('index.html', user=session['user'])

@dashboard_bp.route('/stats')
def stats():
    return jsonify(get_stats())

# --- ALUNOS ROUTES ---
@alunos_bp.route('/list')
def list_alunos():
    alunos = Aluno.get_all()
    data = []
    for a in alunos:
        b = get_boletim(a['id'])
        data.append({
            "id": a['id'],
            "nome": a['nome'],
            "media": b['media'],
            "status": b['status'],
            "qtd_notas": len(b['notas'])
        })
    return jsonify(data)

@alunos_bp.route('/add', methods=['POST'])
def add_aluno():
    nome = request.json.get('nome')
    success, msg = Aluno.create(nome)
    return jsonify({"success": success, "message": msg})

@alunos_bp.route('/remove', methods=['POST'])
def remove_aluno():
    aluno_id = request.json.get('id')
    Aluno.delete(aluno_id)
    return jsonify({"success": True, "message": "Aluno removido."})

@alunos_bp.route('/add_nota', methods=['POST'])
def add_nota():
    aluno_id = request.json.get('id')
    valor = request.json.get('nota')
    success, msg = Nota.add(aluno_id, valor)
    return jsonify({"success": success, "message": msg})
