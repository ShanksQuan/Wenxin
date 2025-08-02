from werkzeug.security import check_password_hash

def verify_password(plain_password, hashed_password):
    """验证密码（与User模型的set_password对应）"""
    return check_password_hash(hashed_password, plain_password)