from flask import Flask
from app.config import Config
from flask import Flask
from app.config import config
from app.extensions import init_extensions
from app.routes import register_routes

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    init_extensions(app)
    
    # 注册路由
    register_routes(app)
    
    return app