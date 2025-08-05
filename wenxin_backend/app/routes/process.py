import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user_info import UserInfo
from app.utils.ai_process import process_text_with_ai, process_image_with_ai

process_bp = Blueprint('process', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@process_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_info():
    """上传信息并进行分类处理"""
    user_id = int(get_jwt_identity())
    
    # 检查是否有文件或文本内容
    if 'file' not in request.files and 'text' not in request.form:
        return jsonify({'error': '没有提供文件或文本内容'}), 400
    
    info_items = []
    user_infos = []  # 存储待提交的用户信息对象
    
    # 处理文件上传
    if 'file' in request.files:
        file = request.files['file']
        if file and allowed_file(file.filename):
            info_type = 'image' if file.filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg'] else 'other'
            
            # 保存文件
            filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
            file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), filename)
            
            # 确保上传目录存在
            os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
            
            file.save(file_path)
            
            # 使用AI处理图片并提取多个信息项
            try:
                extracted_items = process_image_with_ai(file_path)
                
                # 为每个提取的信息项创建数据库记录
                for item in extracted_items:
                    user_info = UserInfo(
                        user_id=user_id,
                        info_type=info_type,
                        content=file_path,
                        category=item['category'],
                        title=item['title'],
                        description=item['description']
                    )
                    db.session.add(user_info)
                    user_infos.append(user_info)  # 添加到待提交列表
                    info_items.append({
                        'title': item['title'],
                        'category': item['category']
                    })
                    
            except Exception as e:
                # 如果AI处理失败，创建一个默认记录
                print(f"AI处理图片时出错: {e}")
                user_info = UserInfo(
                    user_id=user_id,
                    info_type=info_type,
                    content=file_path,
                    category='temporary',
                    title='图片文件',
                    description='上传的图片文件'
                )
                db.session.add(user_info)
                user_infos.append(user_info)  # 添加到待提交列表
                info_items.append({
                    'title': '图片文件',
                    'category': 'temporary'
                })
        
        else:
            return jsonify({'error': '文件类型不支持'}), 400
    
    # 处理文本内容
    elif 'text' in request.form:
        info_type = 'text'
        content = request.form['text']
        
        # 使用AI处理文本并提取多个信息项
        try:
            extracted_items = process_text_with_ai(content)
            
            # 为每个提取的信息项创建数据库记录
            for item in extracted_items:
                user_info = UserInfo(
                    user_id=user_id,
                    info_type=info_type,
                    content=content,
                    category=item['category'],
                    title=item['title'],
                    description=item['description']
                )
                db.session.add(user_info)
                user_infos.append(user_info)  # 添加到待提交列表
                info_items.append({
                    'title': item['title'],
                    'category': item['category']
                })
                
        except Exception as e:
            # 如果AI处理失败，创建一个默认记录
            print(f"AI处理文本时出错: {e}")
            user_info = UserInfo(
                user_id=user_id,
                info_type=info_type,
                content=content,
                category='temporary',
                title='文本内容',
                description=content
            )
            db.session.add(user_info)
            user_infos.append(user_info)  # 添加到待提交列表
            info_items.append({
                'title': '文本内容',
                'category': 'temporary'
            })
    
    db.session.commit()
    
    # 在提交后获取实际的ID并更新返回信息
    for i, user_info in enumerate(user_infos):
        info_items[i]['id'] = user_info.id
    
    return jsonify({
        'message': '信息上传并分类成功',
        'info_items': info_items
    }), 201



@process_bp.route('/info', methods=['GET'])
@jwt_required()
def list_info():
    """列出用户的所有信息，支持分类筛选"""
    user_id = int(get_jwt_identity())
    
    # 获取查询参数
    category = request.args.get('category')
    
    # 构建查询
    query = UserInfo.query.filter_by(user_id=user_id)
    if category:
        query = query.filter_by(category=category)
    
    infos = query.order_by(UserInfo.created_at.desc()).all()
    
    return jsonify([{
        'id': info.id,
        'info_type': info.info_type,
        'title': info.title,
        'description': info.description,
        'category': info.category,
        'created_at': info.created_at.isoformat()
    } for info in infos]), 200

@process_bp.route('/info/<int:info_id>', methods=['GET'])
@jwt_required()
def get_info(info_id):
    """获取特定信息详情"""
    user_id = int(get_jwt_identity())
    
    info = UserInfo.query.filter_by(id=info_id, user_id=user_id).first()
    if not info:
        return jsonify({'error': '信息不存在'}), 404
    
    return jsonify({
        'id': info.id,
        'info_type': info.info_type,
        'content': info.content,
        'category': info.category,
        'title': info.title,
        'description': info.description,
        'created_at': info.created_at.isoformat(),
        'updated_at': info.updated_at.isoformat() if info.updated_at else None
    }), 200