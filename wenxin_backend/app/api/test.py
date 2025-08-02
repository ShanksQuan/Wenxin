from flask import Blueprint,jsonify

# 创建蓝图，URL前缀为/api/test
test_bp = Blueprint('test', __name__, url_prefix='/api/test')

@test_bp.route('hello', methods=['GET'])

def hello():
    """测试接口"""
    return jsonify ({"message": "后端接口测试成功","status": "success"})