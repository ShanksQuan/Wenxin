from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user_info import Conversation, UserInfo, beijing_time
from datetime import timedelta

conversation_bp = Blueprint('conversation', __name__)

@conversation_bp.route('', methods=['POST'])
@jwt_required()
def create_conversation():
    """创建新对话（返回对话ID，用于后续上传信息）"""
    user_id = int(get_jwt_identity())
    # 初始标题可暂定为“新对话”，后续会被首次上传的内容覆盖
    new_conversation = Conversation(
        user_id=user_id,
        title="新对话"
    )
    db.session.add(new_conversation)
    db.session.commit()
    return jsonify({
        'conversation_id': new_conversation.id,
        'title': new_conversation.title,
        'created_at': new_conversation.created_at.isoformat()
    }), 201

@conversation_bp.route('', methods=['GET'])
@jwt_required()
def list_conversations():
    """获取用户的对话列表（支持按时间范围筛选：7天/30天）"""
    user_id = int(get_jwt_identity())
    date_range = request.args.get('date_range')  # 可选参数：7days/30days
    
    # 基础查询：用户的所有对话，按更新时间倒序（最新的在前面）
    query = Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc())
    
    # 时间范围筛选
    if date_range:
        now = beijing_time()
        if date_range == '7days':
            query = query.filter(Conversation.created_at >= now - timedelta(days=7))
        elif date_range == '30days':
            query = query.filter(Conversation.created_at >= now - timedelta(days=30))
        else:
            return jsonify({'error': '时间范围参数无效，支持7days或30days'}), 400
    
    conversations = query.all()
    return jsonify([{
        'id': conv.id,
        'title': conv.title,
        'created_at': conv.created_at.isoformat(),
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
        'info_count': conv.info_items.count()  # 该对话包含的信息项数量
    } for conv in conversations]), 200

@conversation_bp.route('/<int:conv_id>', methods=['GET'])
@jwt_required()
def get_conversation(conv_id):
    """获取单个对话详情（包含该对话下的所有信息项）"""
    user_id = int(get_jwt_identity())
    conversation = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    
    # 获取该对话下的所有信息项（按时间正序排列，模拟对话流）
    info_items = conversation.info_items.order_by(UserInfo.created_at.asc()).all()
    return jsonify({
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
        'info_items': [{
            'id': item.id,
            'info_type': item.info_type,
            'title': item.title,
            'description': item.description,
            'content': item.content,  # 文本内容或图片路径
            'created_at': item.created_at.isoformat()
        } for item in info_items]
    }), 200