from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联用户信息
    user_infos = db.relationship('UserInfo', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

class UserInfo(db.Model):
    """用户信息模型"""
    __tablename__ = 'user_infos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    info_type = db.Column(db.String(32), nullable=False)  # text, image, voice
    content = db.Column(db.Text)  # 文本内容或文件路径
    metadata_info = db.Column(db.JSON)  # 元数据
    vector_id = db.Column(db.String(64))  # 向量数据库ID
    category = db.Column(db.String(32), default='temporary')  # 分类: temporary, meeting, work, finance
    title = db.Column(db.String(255))  # 提取的信息标题
    description = db.Column(db.Text)  # 提取的信息详细描述
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)