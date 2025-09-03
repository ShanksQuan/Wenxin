from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user_info import Conversation, UserInfo, beijing_time, Message
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
    
    # 获取消息记录（按时间正序）
    messages = conversation.messages.order_by(Message.created_at.asc()).all()
    # 获取该对话下的所有信息项（按时间正序排列，模拟对话流）
    info_items = conversation.info_items.order_by(UserInfo.created_at.asc()).all()
    return jsonify({
        'id': conversation.id,
        'title': conversation.title,
        'created_at': conversation.created_at.isoformat(),
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
        'messages': [{
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        } for msg in messages],
        'info_items': [{
            'id': item.id,
            'info_type': item.info_type,
            'title': item.title,
            'description': item.description,
            'content': item.content,  # 文本内容或图片路径
            'created_at': item.created_at.isoformat()
        } for item in info_items]
    }), 200



import dashscope
from flask import current_app
from app.utils.ai_process import detect_savable_info,process_text_with_ai,truncate_context

@conversation_bp.route('/<int:conv_id>/message', methods=['POST'])
@jwt_required()
def send_message(conv_id):
    """发送消息并获取智能体回复（类似大模型对话）"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 验证对话存在且属于用户
    conversation = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conversation:
        return jsonify({'error': '对话不存在'}), 404
    
    # 验证消息内容
    user_message = data.get('content')
    if not user_message:
        return jsonify({'error': '消息内容不能为空'}), 400
    
    # 1. 保存用户消息
    user_msg = Message(
        conversation_id=conv_id,
        user_id=user_id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    
    # 2. 获取历史对话上下文（最近10轮，避免token过长）
    history_messages = conversation.messages.order_by(Message.created_at.asc()).limit(20).all()
    context = [
        {'role': msg.role, 'content': msg.content} 
        for msg in history_messages
    ]
    # 截断上下文至最大token限制（例如1000token）
    context = truncate_context(context, max_tokens=1000)

    # 限制用户输入长度（例如150字符）
    if len(user_message) > 150:
      user_message = user_message[:150] + "..."  # 截断并添加省略号

    # 2.5 检测用户是否发送保存指令
    user_intent = user_message.strip().lower()
    if user_intent in ['保存', '是', '需要保存']:
       # 提取最近对话内容生成待保存文本
       recent_content = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context[-5:]])  # 取最近5条
       # 调用现有文本处理函数生成信息项
       extracted_items = process_text_with_ai(recent_content)
    
       # 保存到UserInfo
       for item in extracted_items:
        user_info = UserInfo(
            user_id=user_id,
            conversation_id=conv_id,
            info_type='text',
            content=recent_content,
            category=item['category'],
            title=item['title'],
            description=item['description']
        )
        db.session.add(user_info)
       db.session.commit()
    
       # 生成确认回复
       assistant_reply = "已为你保存相关信息,可在对话详情中查看。"

       
    # 3. 调用AI生成回复（问心智能体身份）
    try:
        dashscope.api_key = current_app.config.get('DASHSCOPE_API_KEY')
        # 系统提示：定义智能体身份
        system_prompt = """
        你是问心智能体，一个友好的助手。你的主要功能是：
        1. 与用户进行自然对话
        2. 当对话中涉及需要记录的信息（如会议安排、工作任务、财务收支等）时，会提示用户是否需要保存
        3. 回复简洁明了，符合中文表达习惯

        当识别到可保存的信息时，必须在回复末尾添加以下快捷操作提示：
        【如需保存以上信息，请回复"保存"或点击保存按钮】
        """
        
        # 构建对话历史
        messages = [{'role': 'system', 'content': system_prompt}] + context
        messages.append({'role': 'user', 'content': user_message})  # 最新用户消息
        
        # 调用大模型
        response = dashscope.Generation.call(
            model='qwen-plus',
            messages=messages,
            result_format='message'
        )
        assistant_reply = response.output.choices[0].message.content
        
        # 检测是否包含可保存信息（拼接用户消息和初始回复）
        full_conversation = f"用户: {user_message}\n智能体:{assistant_reply}"
        if detect_savable_info(full_conversation):
        # 附加保存询问
            assistant_reply += "\n\n检测到可能需要保存的信息,是否需要为你保存?（回复'是'或'保存'即可）"
        
    except Exception as e:
        print(f"AI回复生成失败: {e}")
        assistant_reply = "抱歉,我暂时无法回复,请稍后再试。"
    
    # 4. 保存智能体回复
    assistant_msg = Message(
        conversation_id=conv_id,
        user_id=user_id,
        role='assistant',
        content=assistant_reply
    )
    db.session.add(assistant_msg)
    
    # 5. 更新对话最后更新时间
    conversation.updated_at = beijing_time()
    db.session.commit()
    
    # 6. 返回结果（包含用户消息和智能体回复）
    return jsonify({
        'user_message': {
            'id': user_msg.id,
            'content': user_msg.content,
            'created_at': user_msg.created_at.isoformat()
        },
        'assistant_reply': {
            'id': assistant_msg.id,
            'content': assistant_msg.content,
            'created_at': assistant_msg.created_at.isoformat()
        }
    }), 201