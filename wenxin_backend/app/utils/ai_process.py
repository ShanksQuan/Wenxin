import openai
import base64
import json
from flask import current_app

def process_text_with_ai(text):
    """
    使用AI处理文本并提取多个信息项
    返回信息项列表，每个包含内容和分类
    """
    try:
        openai.api_key = current_app.config.get('OPENAI_API_KEY')
        
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
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts and categorizes information from text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        result_str = response.choices[0].message.content.strip()
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
        openai.api_key = current_app.config.get('OPENAI_API_KEY')
        
        # 将图片转换为base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        prompt = """
        请分析这张图片中的内容，从中提取出多个独立的信息项，并为每个信息项分配适当的分类。
        
        分类选项：
        1. temporary (临时杂项) - 日常琐事、临时想法等
        2. meeting (会议安排) - 会议时间、地点、议题等
        3. work (工作安排) - 任务、项目、工作计划等
        4. finance (收入支出) - 费用、收入、预算等
        
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
        
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        result_str = response.choices[0].message.content.strip()
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