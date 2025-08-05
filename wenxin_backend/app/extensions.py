from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager


# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def init_extensions(app):
    """初始化所有扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # 将TokenBlocklist的导入移到函数内部，避免循环导入
    from app.models.user_info import TokenBlocklist

    # 添加JWT回调函数
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
        return token is not None