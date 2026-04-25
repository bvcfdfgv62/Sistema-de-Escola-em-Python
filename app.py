from flask import Flask
from db import init_db, close_db
from routes import auth_bp, dashboard_bp, alunos_bp
import os

def create_app():
    app = Flask(__name__)
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'triadcode-super-secret-key-2024'
    app.config['DEBUG'] = True
    
    # Inicialização do Banco
    init_db()
    
    # Registro de Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(alunos_bp)
    
    # Gerenciamento de Conexão
    app.teardown_appcontext(close_db)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=3000)
