import sqlite3
import os
from flask import g, has_app_context
from werkzeug.security import generate_password_hash, check_password_hash

# Configurações de Banco de Dados
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'escola.db')

def get_db():
    """Retorna uma conexão com o banco de dados, gerenciando o contexto do Flask se necessário."""
    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
            g.db.execute('PRAGMA foreign_keys = ON')
        return g.db
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

def close_db(e=None):
    """Fecha a conexão do Flask."""
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()

def init_db():
    """Inicializa as tabelas e o usuário administrador padrão."""
    db = sqlite3.connect(DB_PATH)
    db.execute('CREATE TABLE IF NOT EXISTS alunos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY AUTOINCREMENT, aluno_id INTEGER, valor REAL NOT NULL, FOREIGN KEY (aluno_id) REFERENCES alunos (id) ON DELETE CASCADE)')
    db.execute('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, senha TEXT NOT NULL)')
    db.commit()
    
    # Criar admin se não existir
    cursor = db.execute('SELECT * FROM usuarios WHERE username = ?', ('admin',))
    if not cursor.fetchone():
        hash_pw = generate_password_hash('1234')
        db.execute('INSERT INTO usuarios (username, senha) VALUES (?, ?)', ('admin', hash_pw))
        db.commit()
    db.close()

# --- Lógica de Negócio (Modelos Simplificados) ---

class Aluno:
    @staticmethod
    def create(nome):
        db = get_db()
        try:
            db.execute('INSERT INTO alunos (nome) VALUES (?)', (nome.strip(),))
            db.commit()
            res = (True, "Aluno cadastrado com sucesso.")
        except sqlite3.IntegrityError:
            res = (False, "Este aluno já existe.")
        finally:
            if not has_app_context(): db.close()
        return res

    @staticmethod
    def get_all():
        db = get_db()
        res = db.execute('SELECT * FROM alunos ORDER BY nome ASC').fetchall()
        if not has_app_context(): db.close()
        return res

    @staticmethod
    def delete(aluno_id):
        db = get_db()
        db.execute('DELETE FROM alunos WHERE id = ?', (aluno_id,))
        db.commit()
        if not has_app_context(): db.close()
        return True

class Nota:
    @staticmethod
    def add(aluno_id, valor):
        db = get_db()
        try:
            db.execute('INSERT INTO notas (aluno_id, valor) VALUES (?, ?)', (aluno_id, float(valor)))
            db.commit()
            res = (True, "Nota adicionada com sucesso.")
        except (ValueError, sqlite3.Error):
            res = (False, "Erro ao adicionar nota. Verifique o valor.")
        finally:
            if not has_app_context(): db.close()
        return res

    @staticmethod
    def get_by_aluno(aluno_id):
        db = get_db()
        res = db.execute('SELECT valor FROM notas WHERE aluno_id = ?', (aluno_id,)).fetchall()
        if not has_app_context(): db.close()
        return res

class Usuario:
    @staticmethod
    def verify(username, password):
        db = get_db()
        user = db.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        if not has_app_context(): db.close()
        if user and check_password_hash(user['senha'], password):
            return user
        return None

# --- Funções Utilitárias (Compatibilidade com Sistema e GUI) ---

def get_boletim(aluno_id):
    notas = [n['valor'] for n in Nota.get_by_aluno(aluno_id)]
    if not notas: return {"notas": [], "media": 0.0, "status": "Sem Notas"}
    media = sum(notas) / len(notas)
    status = "APROVADO" if media >= 7 else "RECUPERAÇÃO" if media >= 5 else "REPROVADO"
    return {"notas": notas, "media": round(media, 1), "status": status}

def get_stats():
    alunos = Aluno.get_all()
    medias = []
    aprovados = 0
    for a in alunos:
        b = get_boletim(a['id'])
        if b['status'] != "Sem Notas":
            medias.append(b['media'])
            if b['status'] == "APROVADO": aprovados += 1
    return {
        "total": len(alunos), 
        "media_geral": round(sum(medias)/len(medias), 1) if medias else 0.0, 
        "aprovados": aprovados
    }

# Aliases para compatibilidade direta com gui_premium.py
cadastrar_aluno = Aluno.create
listar_alunos = Aluno.get_all
remover_aluno = Aluno.delete
adicionar_nota = Nota.add
validar_acesso = lambda u, p: Usuario.verify(u, p) is not None
