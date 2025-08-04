from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user_info import User
from app.extensions import db
from app.utils.auth import verify_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.post('/register')
def register():
    """用户注册"""
    data = request.get_json()
    if not all(k in data for k in ['username', 'password', 'email']):
        return jsonify({'error': '缺少必要字段'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': '用户名已存在'}), 409
    
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': '注册成功'}), 201

@auth_bp.post('/login')
def login():
    """用户登录"""
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()
    
    if not user or not verify_password(data.get('password'), user.password_hash):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token), 200