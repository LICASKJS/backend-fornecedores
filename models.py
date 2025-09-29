from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Fornecedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    cnpj = db.Column(db.String(14), unique=True, nullable=False)
    senha = db.Column(db.String(256), nullable=False) 
    documentos = db.relationship('Documento', backref='fornecedor', lazy=True)
    dados_homologacao = db.relationship('Homologacao', backref='fornecedor', lazy=True)
    categoria = db.Column(db.String(100))
    token_recuperacao = db.Column(db.String(6), nullable=True)
    token_expira = db.Column(db.DateTime, nullable=True)

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_documento = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=False)

class Homologacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    iqf = db.Column(db.Float, nullable=False)
    homologacao = db.Column(db.String(50), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)  
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=False)

    