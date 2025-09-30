import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key-here'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://usuario:senha@localhost:5432/fornecedores_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.office365.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'notificacaosuprimentos@engeman.net'  
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '02082023Ll*' 
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME') or 'notificacaosuprimentos@engeman.net'
