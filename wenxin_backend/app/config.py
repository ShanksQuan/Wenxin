import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_EXPIRATION_DELTA', 86400))
    
    # 服务配置
    VECTOR_DB_URL = os.getenv('VECTOR_DB_URL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    SPEECH_API_KEY = os.getenv('SPEECH_RECOGNITION_API_KEY')
    OCR_API_KEY = os.getenv('OCR_API_KEY')
    
    # 安全配置
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')

    # 文件上传配置
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    
class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}