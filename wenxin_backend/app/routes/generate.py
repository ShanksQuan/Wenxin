# app/routes/generate.py
from flask import Blueprint

# 创建生成模块的蓝图（命名为 generate_bp，与导入名称一致）
generate_bp = Blueprint('generate', __name__)

# 预留生成相关接口示例（可选）
# @generate_bp.route('/text', methods=['POST'])
# def generate_text():
#     # 文本生成逻辑
#     return jsonify({"generated_text": "示例内容"}), 200