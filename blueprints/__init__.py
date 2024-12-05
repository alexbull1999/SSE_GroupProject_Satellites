from .country import country_bp
from .login import login_bp
from .satellites import satellites_bp
from .search import search_bp
from .account import account_bp

def register_blueprints(app):
    app.register_blueprint(country_bp)
    app.register_blueprint(login_bp)
    app.register_blueprint(satellites_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(account_bp)
