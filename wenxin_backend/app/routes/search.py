# app/routes/search.py
from flask import Blueprint

# 创建搜索模块的蓝图（必须命名为 search_bp，与导入时的名称一致）
search_bp = Blueprint('search', __name__)

# 预留搜索相关的接口，例如：
# @search_bp.route('/query', methods=['GET'])
# def search_query():
#     # 搜索逻辑实现
#     return jsonify({"result": "搜索结果"}), 200