from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .config import SECRET_KEY
from .models.migrations import init_db

csrf = CSRFProtect()

def create_app():
    # Run migrations/init database
    init_db()
    
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.secret_key = SECRET_KEY
    
    csrf.init_app(app)
    
    # Blueprints will be registered here
    from .web.routes.study import study_bp
    from .web.routes.cards import cards_bp
    from .web.routes.decks import decks_bp
    app.register_blueprint(study_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(decks_bp)
    
    # Add a root redirect to decks index
    @app.route('/')
    def index():
        from flask import redirect, url_for
        return redirect(url_for('decks.index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=10000)
