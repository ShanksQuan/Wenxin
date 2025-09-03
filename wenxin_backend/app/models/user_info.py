from app.extensions import db
from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash

#获取北京时间
def beijing_time():
    return datetime.utcnow() + timedelta(hours=8)

# 对话模型（管理单个对话）
class Conversation(db.Model):
    """对话模型（包含多个UserInfo信息项）"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 关联用户
    title = db.Column(db.String(255), nullable=False)  # 对话标题（取自首次上传内容）
    created_at = db.Column(db.DateTime, default=beijing_time)  # 对话创建时间（北京时间）
    updated_at = db.Column(db.DateTime, onupdate=beijing_time)  # 最后更新时间
    
    # 关联该对话下的所有信息项
    info_items = db.relationship('UserInfo', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')



class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=beijing_time)
    
    # 关联用户信息
    user_infos = db.relationship('UserInfo', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

class UserInfo(db.Model):
    """用户信息模型"""
    __tablename__ = 'user_infos'
    
    # 新增：关联对话的外键
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    info_type = db.Column(db.String(32), nullable=False)  # text, image, voice
    content = db.Column(db.Text)  # 文本内容或文件路径
    metadata_info = db.Column(db.JSON)  # 元数据
    vector_id = db.Column(db.String(64))  # 向量数据库ID
    category = db.Column(db.String(32), default='temporary')  # 分类: temporary, meeting, work, finance
    title = db.Column(db.String(255))  # 提取的信息标题
    description = db.Column(db.Text)  # 提取的信息详细描述
    created_at = db.Column(db.DateTime, default=beijing_time)
    updated_at = db.Column(db.DateTime, onupdate=beijing_time)

class TokenBlocklist(db.Model):
    """Token黑名单模型"""
    __tablename__ = 'token_blocklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=beijing_time, nullable=False)


class Message(db.Model):
    """对话消息模型（用户与智能体的交互内容）"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)  # 关联对话
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 关联用户
    role = db.Column(db.String(10), nullable=False)  # 角色：user/assistant
    content = db.Column(db.Text, nullable=False)  # 消息内容
    created_at = db.Column(db.DateTime, default=beijing_time)  # 消息时间
    
    # 关联关系
    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy='dynamic', cascade='all, delete-orphan'))