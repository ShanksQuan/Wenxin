import json
from flask import current_app
# Deleted: import openai
# Deleted: import base64
import dashscope
from dashscope import Generation
import base64

def process_text_with_ai(text):
    """
    使用AI处理文本并提取多个信息项
    返回信息项列表，每个包含内容和分类
    """
    try:
        # Deleted: openai.api_key = current_app.config.get('OPENAI_API_KEY')
        dashscope.api_key = current_app.config.get('DASHSCOPE_API_KEY')
        
        prompt = f"""
        请分析以下文本内容，从中提取出多个独立的信息项，并为每个信息项分配适当的分类。
        
        分类选项：
        1. temporary (临时杂项) - 日常琐事、临时想法等
        2. meeting (会议安排) - 会议时间、地点、议题等
        3. work (工作安排) - 任务、项目、工作计划等
        4. finance (收入支出) - 费用、收入、预算等
        
        文本内容：
        "{text}"
        
        请按照以下JSON格式返回结果：
        [
          {{
            "title": "信息项标题",
            "description": "信息项详细描述",
            "category": "temporary|meeting|work|finance"
          }},
          ...
        ]
        
        只返回JSON数组，不要包含其他内容。
        """
        
    
        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant that extracts and categorizes information from text.'},
            {'role': 'user', 'content': prompt}
        ]
        response = Generation.call(
            model='qwen-plus',
            messages=messages,
            result_format='message'
        )
        
        
        result_str = response.output.choices[0].message.content.strip()
        # 移除可能的markdown代码块标记
        if result_str.startswith("```"):
            result_str = result_str.split("\n", 1)[1]
            if result_str.endswith("```"):
                result_str = result_str[:-3]
        
        items = json.loads(result_str)
        
        # 验证分类
        valid_categories = ['temporary', 'meeting', 'work', 'finance']
        for item in items:
            if item.get('category') not in valid_categories:
                item['category'] = 'temporary'
        
        return items
            
    except Exception as e:
        print(f"AI文本处理错误: {e}")
        # 出错时返回默认项
        return [{
            'title': '原始文本',
            'description': text,
            'category': 'temporary'
        }]

def process_image_with_ai(image_path):
    """
    使用AI处理图片并提取多个信息项
    返回信息项列表，每个包含内容和分类
    """
    try:
        
        dashscope.api_key = current_app.config.get('DASHSCOPE_API_KEY')
        
        # 将图片转换为base64
        
        # 构建文件路径（根据操作系统）
        if os.name == 'nt':  # Windows系统
            file_url = f"file:///{image_path}"
        else:  # Linux或macOS系统
            file_url = f"file://{image_path}"
        
        prompt = """
        请分析这张图片中的内容，从中提取出多个独立的信息项，并为每个信息项分配适当的分类。
        
        分类选项：
        1. temporary (临时杂项) - 日常琐事、临时想法、便签、随手记录等
        2. meeting (会议安排) - 会议时间、地点、议题、参会人员、会议记录等
        3. work (工作安排) - 任务清单、项目计划、工作进度、待办事项、工作笔记等
        4. finance (收入支出) - 发票、收据、账单、预算表、费用明细、工资条等

        要求：
        1. 仔细识别图片中的文字内容和语义信息
        2. 每个信息项应该是一个完整的、有意义的信息单元
        3. 标题应该简洁明了，描述应该详细准确
        4. 严格按照上述4个分类进行归类，不要创造新的分类
        5. 如果无法识别有效信息，请返回空数组[]
        
        请按照以下JSON格式返回结果：
        [
          {
            "title": "信息项标题",
            "description": "信息项详细描述",
            "category": "temporary|meeting|work|finance"
          },
          ...
        ]
        
        只返回JSON数组，不要包含其他内容。
        """
        
        
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": prompt},
                    {"image": file_url}
                ]
            }
        ]
        response = Generation.call(
            model='qwen-vl-ocr',
            messages=messages,
            result_format='message',
            temperature=0.7,        # 对于OCR任务，较低的temperature更好
            top_p=0.8,
            top_k=50,
            max_tokens=1500,        # OCR需要更多token
            repetition_penalty=1.05
        )
        
        # Deleted: result_str = response.choices[0].message.content.strip()
        result_str = response.output.choices[0].message.content.strip()
        # 移除可能的markdown代码块标记
        if result_str.startswith("```"):
            result_str = result_str.split("\n", 1)[1]
            if result_str.endswith("```"):
                result_str = result_str[:-3]
        
        items = json.loads(result_str)
        
        # 验证分类
        valid_categories = ['temporary', 'meeting', 'work', 'finance']
        for item in items:
            if item.get('category') not in valid_categories:
                item['category'] = 'temporary'
        
        return items
            
    except Exception as e:
        print(f"AI图片处理错误: {e}")
        # 出错时返回默认项
        return [{
            'title': '图片内容',
            'description': '从图片中提取的内容',
            'category': 'temporary'
        }]