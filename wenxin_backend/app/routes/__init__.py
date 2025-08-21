from app.routes.auth import auth_bp
from app.routes.info import info_bp
from app.routes.search import search_bp
from app.routes.generate import generate_bp
from app.routes.process import process_bp
from app.routes.conversation import conversation_bp
def register_routes(app):
    """注册所有路由蓝图"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(info_bp, url_prefix='/api/info')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(generate_bp, url_prefix='/api/generate')
    app.register_blueprint(process_bp, url_prefix='/api/process')
    app.register_blueprint(conversation_bp, url_prefix='/api/conversation')