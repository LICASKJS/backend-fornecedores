from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from flask_mail import Mail, Message
from config import Config
from models import db, Fornecedor, Documento, Homologacao
from werkzeug.security import generate_password_hash, check_password_hash
import random
import base64
import os
import pandas as pd 
from flask_cors import CORS 
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename



mail = Mail()

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config.from_object(Config)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})


CORS(app)  

db.init_app(app)
jwt = JWTManager(app)
mail.init_app(app)  

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Bem-vindo ao Portal de Fornecedores!"


@app.route('/api/cadastro', methods=['POST'])
def cadastrar_fornecedor():
    try:
        data = request.get_json()
        print(data)  
        
        if not all(key in data for key in ('email', 'cnpj', 'nome', 'senha')):
            return jsonify(message="Dados incompletos, verifique os campos."), 400

        hashed_password = generate_password_hash(data['senha'], method='pbkdf2:sha256')

        fornecedor = Fornecedor(
            nome=data['nome'],
            email=data['email'],
            cnpj=data['cnpj'],
            senha=hashed_password
        )

        db.session.add(fornecedor)
        db.session.commit()

        return jsonify(message="Fornecedor cadastrado com sucesso"), 201
    except Exception as e:
        print(str(e))  
        return jsonify(message="Erro ao cadastrar fornecedor: " + str(e)), 500


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get("email")
        senha = data.get("senha")  

        fornecedor = Fornecedor.query.filter_by(email=email).first()

        if fornecedor and check_password_hash(fornecedor.senha, senha):
            access_token = create_access_token(identity=fornecedor.id)
            return jsonify(access_token=access_token), 200

        return jsonify(message="Credenciais inválidas"), 401

    except Exception as e:
        print(f"Erro no login: {e}")
        return jsonify(message="Erro ao autenticar"), 500
    

@app.route('/api/recuperar-senha', methods=['POST'])
def recuperar_senha():
    try:
        data = request.get_json()
        fornecedor = Fornecedor.query.filter_by(email=data['email']).first()

        if not fornecedor:
            return jsonify(message="Fornecedor não encontrado"), 404

        token = str(random.randint(100000, 999999))
        fornecedor.token_recuperacao = token
        fornecedor.token_expira = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        corpo_email = f"""
  <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recuperação de Senha - Engeman</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Inter', Arial, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                
                <div style="background: white; border-radius: 12px; padding: 40px 30px; text-align: center; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); margin-bottom: 20px;">
                    <img src="cid:engeman_logo" alt="Engeman Logo" style="max-width: 200px; height: auto; margin-bottom: 20px;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: 600; color: #f97316;">
                        RECUPERAÇÃO DE SENHA
                    </h1> <br>                
                    <h2 style="margin: 0 0 20px 0; font-size: 20px; font-weight: 600; color: #696969;">
                        Olá, {fornecedor.nome}!
                    </h2>
                    
                    <p style="margin: 0 0 30px 0; color: #64748b; font-size: 16px; line-height: 1.6;">
                        Recebemos uma solicitação para redefinir a senha da sua conta. Use o token abaixo para criar uma nova senha:
                    </p>

                    <div style="background: #fef3c7; border: 2px solid #f97316; border-radius: 8px; padding: 25px; margin: 30px 0; text-align: center;">
                        <p style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #92400e;">
                            Seu Token de Recuperação:
                        </p>
                        <div style="font-size: 32px; font-weight: 600; color: #f97316; letter-spacing: 4px; font-family: 'Courier New', monospace; margin: 15px 0;">
                            {token}
                        </div>
                        <p style="margin: 15px 0 0 0; color: #92400e; font-size: 14px;">
                            Este token expira em 10 minutos
                        </p>
                    </div>

                    <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; margin: 30px 0;">
                        <h4 style="margin: 0 0 15px 0; font-size: 16px; font-weight: 600; color: #1e293b;">
                            Como usar:
                        </h4>
                        <ol style="margin: 0; color: #64748b; font-size: 14px; line-height: 1.6; padding-left: 20px;">
                            <li>Acesse a página de recuperação de senha</li>
                            <li>Digite o token no campo solicitado</li>
                            <li>Defina sua nova senha</li>
                        </ol>
                    </div>

                    <p style="margin: 30px 0 0 0; color: #94a3b8; font-size: 14px; text-align: center;">
                        Se você não solicitou esta recuperação, ignore este e-mail.
                    </p>

                    <!-- Simplified footer -->
                    <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0; margin-top: 30px;">
                        <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                            © 2025 Engeman - Portal de Fornecedores
                        </p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        imagem_path = os.path.join(os.path.dirname(app.root_path), 'static', 'colorida.png')
        enviar_email(fornecedor.email, "Recuperação de Senha", corpo_email, imagem_path)

        return jsonify(message="Token de recuperação enviado por e-mail"), 200

    except Exception as e:
        return jsonify(message="Erro ao recuperar senha: " + str(e)), 500

@app.route("/api/validar-token", methods=["POST"])
def validar_token():
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify(message="Token é obrigatório"), 400

        fornecedor = Fornecedor.query.filter_by(token_recuperacao=token).first()
        if not fornecedor:
            return jsonify(message="Token inválido ou fornecedor não encontrado"), 404

        if fornecedor.token_expira < datetime.utcnow():
            return jsonify(message="Token expirado"), 400

        return jsonify(message="Token válido"), 200

    except Exception as e:
        print(f"Erro ao validar token: {e}")
        return jsonify(message="Erro ao validar token"), 500

@app.route("/api/redefinir-senha", methods=["POST"])
def redefinir_senha():
    data = request.get_json()
    token = data.get("token")
    nova_senha = data.get("nova_senha")

    if not token or not nova_senha:
        return jsonify(message="Token e nova senha são obrigatórios"), 400

    fornecedor = Fornecedor.query.filter_by(token_recuperacao=token).first()
    if not fornecedor:
        return jsonify(message="Token inválido ou fornecedor não encontrado"), 404

    if fornecedor.token_expira < datetime.utcnow():  
        return jsonify(message="Token expirado"), 400

    fornecedor.senha = generate_password_hash(nova_senha, method="pbkdf2:sha256")
    fornecedor.token_recuperacao = None
    fornecedor.token_expira = None
    db.session.commit()

    return jsonify(message="Senha redefinida com sucesso"), 200


@app.route('/api/contato', methods=['POST'])
def contato():
    try:
        data = request.get_json()
        nome = data.get("nome")
        email = data.get("email")
        assunto = data.get("assunto")
        mensagem = data.get("mensagem")

        if not nome or not email or not assunto or not mensagem:
            return jsonify(message="Todos os campos são obrigatórios."), 400

        corpo_email = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MENSAGEM DO PORTAL DE FORNECEDORES</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }}
        
        .header {{
            background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
            padding: 40px 30px;
            text-align: center;
            position: relative;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
        }}
        
        .logo {{
            width: 150px;
            height: auto;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }}
        
        .header-title {{
            color: #f97316;
            font-size: 24px;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            position: relative;
            z-index: 1;
        }}
        
        .content {{
            padding: 40px 30px;
        }}
        
        .message-card {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            border-left: 4px solid #f97316;
        }}
        
        .field {{
            margin-bottom: 20px;
        }}
        
        .field-label {{
            display: inline-flex;
            align-items: center;
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            font-size: 14px;
        }}
        
        .field-icon {{
            width: 16px;
            height: 16px;
            margin-right: 8px;
            color: #f97316;
        }}
        
        .field-value {{
            color: #475569;
            font-size: 15px;
            line-height: 1.6;
            background: #ffffff;
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }}
        
        .message-text {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .footer {{
            background: #f1f5f9;
            padding: 24px 30px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}
        
        .footer-text {{
            color: #64748b;
            font-size: 13px;
            line-height: 1.5;
        }}
        
        .badge {{
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
            color: #000000;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 21px;
            font-weight: 600;
            margin-bottom: 16px;
        }}
        
        @media (max-width: 600px) {{
            .container {{
                margin: 10px;
                border-radius: 12px;
            }}
            
            .header, .content, .footer {{
                padding-left: 20px;
                padding-right: 20px;
            }}
            
            .header-title {{
                font-size: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <img src="cid:engeman_logo" alt="Engeman Logo" class="logo">
            <h1 class="header-title">PORTAL DE FORNECEDORES</h1>
            <p>Abaixo tem algumas dúvidas do fornecedor, favor analise o quanto antes</p>
        </div>
        
        <div class="content">
            <div class="badge">
                📧 Nova Mensagem Recebida
            </div>
            
            <div class="message-card">
                <div class="field">
                    <div class="field-label">
                        <svg class="field-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd"/>
                        </svg>
                        Nome do Remetente
                    </div>
                    <div class="field-value">{nome}</div>
                </div>
                
                <div class="field">
                    <div class="field-label">
                        <svg class="field-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                            <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                        </svg>
                        E-mail de Contato
                    </div>
                    <div class="field-value">{email}</div>
                </div>
                
                <div class="field">
                    <div class="field-label">
                        <svg class="field-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 101 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
                        </svg>
                        Assunto
                    </div>
                    <div class="field-value">{assunto}</div>
                </div>
                
                <div class="field">
                    <div class="field-label">
                        <svg class="field-icon" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clip-rule="evenodd"/>
                        </svg>
                        Mensagem
                    </div>
                    <div class="field-value message-text">{mensagem}</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p class="footer-text">
                <strong>Portal de Fornecedores</strong><br>
                Este é um e-mail automático gerado pelo sistema. Por favor, não responda diretamente a esta mensagem.
            </p>
        </div>
    </div>
</body>
</html>
"""

        imagem_path = os.path.join(os.path.dirname(app.root_path), 'static', 'colorida.png')
        

        enviar_email(
            destinatario="lucas.mateus@engeman.net",
            assunto=f"MENSAGEM DO PORTAL: {assunto}",
            corpo=corpo_email,
            imagem_path=imagem_path
        )

        

        return jsonify(message="Mensagem enviada com sucesso!"), 200

    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")
        return jsonify(message="Erro ao enviar a mensagem."), 500
    



def allowed_file(filename):
    allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'xlsx', 'csv']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/api/envio-documento', methods=['POST'])
def enviar_documento():
    try:
        fornecedor_id = request.form.get('fornecedor_id')
        categoria = request.form.get('categoria')
        arquivos = request.files.getlist('arquivos')

        fornecedor = Fornecedor.query.get(fornecedor_id)
        if not fornecedor:
            return jsonify(message="Fornecedor não encontrado"), 404

        if not categoria or not arquivos:
            return jsonify(message="Categoria ou arquivos não fornecidos"), 400

        pasta_fornecedor = os.path.join(UPLOAD_FOLDER, str(fornecedor_id))
        os.makedirs(pasta_fornecedor, exist_ok=True)

        lista_arquivos = []
        arquivos_paths = []  

        documentos = []

        for arquivo in arquivos:
            if not allowed_file(arquivo.filename):
                return jsonify(message=f"Extensão do arquivo não permitida: {arquivo.filename}"), 400

            filename = secure_filename(arquivo.filename)
            caminho_arquivo = os.path.join(pasta_fornecedor, filename)
            arquivo.save(caminho_arquivo)

            documento = Documento(
                nome_documento=filename,
                categoria=categoria,
                fornecedor_id=fornecedor.id
            )

            documentos.append(documento)
            lista_arquivos.append(filename)
            arquivos_paths.append(caminho_arquivo)

        db.session.add_all(documentos)
        db.session.commit()

        link_documentos = [f"/uploads/{fornecedor_id}/{a}" for a in lista_arquivos]

        enviar_email_documento(
            fornecedor_nome=fornecedor.nome,
            documento_nome=", ".join(lista_arquivos),
            categoria=categoria,
            destinatario='lucas.mateus@engeman.net',
            link_documento=", ".join(link_documentos),
            arquivos_paths=arquivos_paths
        )

        return jsonify(message="Documentos enviados com sucesso", enviados=lista_arquivos), 200

    except Exception as e:
        import traceback
        print("Erro no envio de documentos:", traceback.format_exc())
        return jsonify(message="Erro ao enviar documentos: " + str(e)), 500
    

@app.route('/api/documentos-necessarios', methods=['POST'])
def documentos_necessarios():
    import pandas as pd
    import os

    try:
        data = request.get_json()
        categoria = data.get('categoria')

        if not categoria:
            return jsonify(message="Categoria não fornecida"), 400

        claf_path = os.path.abspath(os.path.join(app.root_path, '..', 'uploads', 'CLAF.xlsx'))
        
        if not os.path.exists(claf_path):
            return jsonify(message="Planilha CLAF não encontrada"), 500

        df = pd.read_excel(claf_path, header=0)

        df.columns = df.columns.str.strip().str.replace('\n', '').str.replace('\r', '')

        if 'MATERIAL' not in df.columns:
            return jsonify(message="Coluna 'MATERIAL' não encontrada na planilha"), 500

        df_filtrado = df[df['MATERIAL'].str.upper().str.contains(categoria.upper().strip(), na=False)]

        documentos = []

        for _, row in df_filtrado.iterrows():
            if 'REQUISITOS LEGAIS' in df.columns and pd.notna(row['REQUISITOS LEGAIS']):
                documentos.append(row['REQUISITOS LEGAIS'])

        return jsonify(documentos=documentos), 200

    except Exception as e:
        return jsonify(message="Erro ao consultar documentos: " + str(e)), 500


@app.route('/api/dados-homologacao', methods=['GET'])
def consultar_dados_homologacao():
    try:
        fornecedor_id = request.args.get('fornecedor_id', type=int)

        if not fornecedor_id:
            return jsonify(message="Parâmetro 'fornecedor_id' é obrigatório."), 400

        path_homologados = os.path.abspath(os.path.join(app.root_path, '..', 'uploads', 'fornecedores_homologados.xlsx'))
        path_controle = os.path.abspath(os.path.join(app.root_path, '..', 'uploads', 'atendimento_controle_qualidade.xlsx'))

        if not os.path.exists(path_homologados) or not os.path.exists(path_controle):
            return jsonify(message="Um ou mais arquivos de planilha não foram encontrados. Verifique os caminhos dos arquivos."), 500

        df_homologacao = pd.read_excel(path_homologados)
        df_controle_qualidade = pd.read_excel(path_controle)

        df_homologacao.columns = df_homologacao.columns.str.strip().str.lower().str.replace(" ", "_")
        df_controle_qualidade.columns = df_controle_qualidade.columns.str.strip().str.lower().str.replace(" ", "_")

        filtro_homologados = df_homologacao[df_homologacao['id'] == fornecedor_id]
        
        if filtro_homologados.empty:
            return jsonify(message="Fornecedor não encontrado na planilha de homologados."), 404

        fornecedor_h = filtro_homologados.iloc[0]
        nota_homologacao = fornecedor_h.get('nota_homologacao', None)
        iqf = fornecedor_h.get('iqf', None)

        filtro_ocorrencias = df_controle_qualidade[df_controle_qualidade['nome_agente'] == fornecedor_h['nome_fantasia']]
        observacoes_lista = filtro_ocorrencias['observacao'].dropna().tolist()

        return jsonify(
            id=fornecedor_h['id'],
            nome=fornecedor_h['nome_fantasia'],
            iqf=iqf,
            homologacao=nota_homologacao,
            ocorrencias=observacoes_lista
        ), 200

    except FileNotFoundError as fnf:
        return jsonify(message=f"Arquivo de planilha não encontrado: {str(fnf)}"), 500
    except Exception as e:
        return jsonify(message="Erro ao consultar dados de homologação", error_details=str(e)), 500



@app.route('/api/fornecedores', methods=['GET'])
def listar_fornecedores():
    nome = request.args.get('nome', '')  
    print(f"Buscando fornecedores com nome: {nome}")  

    if nome:
        fornecedores = Fornecedor.query.filter(Fornecedor.nome.ilike(f'%{nome}%')).all()  
    else:
        fornecedores = Fornecedor.query.all()  

    print(f"Fornecedores encontrados: {len(fornecedores)}")  

    lista = [{"id": f.id, "nome": f.nome, "email": f.email, "cnpj": f.cnpj} for f in fornecedores]
    return jsonify(lista)

def enviar_email_documento(fornecedor_nome, documento_nome, categoria, destinatario, link_documento, arquivos_paths=None):
    
    corpo = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MENSAGEM DO PORTAL DE FORNECEDORES</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 16px;
                overflow: hidden;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }}
            
            .header {{
                background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
                padding: 40px 30px;
                text-align: center;
                position: relative;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="0.5"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>');
            }}
            
            .logo {{
                width: 150px;
                height: auto;
                margin-bottom: 20px;
                position: relative;
                z-index: 1;
                filter: brightness(0) invert(1);
            }}
            
            .header-title {{
                color: #f97316;
                font-size: 24px;
                font-weight: 700;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                position: relative;
                z-index: 1;
            }}
            
            .content {{
                padding: 40px 30px;
            }}
            
            .badge {{
                display: inline-flex;
                align-items: center;
                background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
                color: #000000;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 16px;
            }}
            
            .message-card {{
                background: #f8fafc;
                border-radius: 12px;
                padding: 24px;
                margin-bottom: 24px;
                border-left: 4px solid #f97316;
            }}
            
            .message-title {{
                font-size: 20px;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 16px;
            }}
            
            .message-text {{
                color: #475569;
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 20px;
            }}
            
            .field {{
                margin-bottom: 20px;
            }}
            
            .field-label {{
                display: inline-flex;
                align-items: center;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 8px;
                font-size: 14px;
            }}
            
            .field-icon {{
                width: 16px;
                height: 16px;
                margin-right: 8px;
                color: #f97316;
            }}
            
            .field-value {{
                color: #475569;
                font-size: 15px;
                line-height: 1.6;
                background: #ffffff;
                padding: 12px 16px;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                font-weight: 500;
            }}
            
            .cta-section {{
                text-align: center;
                margin: 32px 0;
                padding: 24px;
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border-radius: 12px;
                border: 1px solid #f59e0b;
            }}
            
            .cta-text {{
                font-size: 16px;
                color: #92400e;
                margin-bottom: 16px;
                font-weight: 500;
            }}
            
            .cta-button {{
                display: inline-flex;
                align-items: center;
                background: linear-gradient(135deg, #f97316 0%, #ef4444 100%);
                color: #ffffff;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                font-size: 15px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(249, 115, 22, 0.3);
            }}
            
            .cta-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(249, 115, 22, 0.4);
            }}
            
            .footer {{
                background: #f1f5f9;
                padding: 24px 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            
            .footer-text {{
                color: #64748b;
                font-size: 13px;
                line-height: 1.5;
                margin-bottom: 8px;
            }}
            
            .company-info {{
                color: #94a3b8;
                font-size: 12px;
                font-weight: 500;
                margin-top: 16px;
            }}
            
            /* Dark mode support for better readability */
            @media (prefers-color-scheme: dark) {{
                .container {{
                    background: #1e293b;
                    color: #f1f5f9;
                }}
                
                .message-card {{
                    background: #334155;
                    border-left-color: #f97316;
                }}
                
                .message-title {{
                    color: #f1f5f9;
                }}
                
                .message-text {{
                    color: #cbd5e1;
                }}
                
                .field-label {{
                    color: #f1f5f9;
                }}
                
                .field-value {{
                    background: #475569;
                    color: #f1f5f9;
                    border-color: #64748b;
                }}
                
                .footer {{
                    background: #334155;
                    border-top-color: #475569;
                }}
                
                .footer-text {{
                    color: #94a3b8;
                }}
                
                .company-info {{
                    color: #64748b;
                }}
            }}
            
            @media (max-width: 600px) {{
                .container {{
                    margin: 10px;
                    border-radius: 12px;
                }}
                
                .header, .content, .footer {{
                    padding-left: 20px;
                    padding-right: 20px;
                }}
                
                .header-title {{
                    font-size: 20px;
                }}
                
                .cta-section {{
                    padding: 20px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="header-title"> DOCUMENTAÇÕES DO FORNECEDOR </h1>
            </div>
            
            <div class="content">
                <div class="badge">
                    📄 Novas Documentações Recebidas
                </div>
                
                <div class="message-card">
                    <h2 class="message-title">Documentação de Fornecedor</h2>
                    <p class="message-text">
                        O fornecedor <strong>{fornecedor_nome}</strong> enviou os documentos necessários para cadastro e homologação no sistema.
                    </p>
                    
                    <div class="field">
                        <div class="field-label">
                            <span class="field-icon">📋</span>
                            DOCUMENTO
                        </div>
                        <div class="field-value">{documento_nome}</div>
                    </div>
                    
                    <div class="field">
                        <div class="field-label">
                            <span class="field-icon">🏷️</span>
                            CATEGORIA
                        </div>
                        <div class="field-value">{categoria}</div>
                    </div>
                </div>
                
                <div class="cta-section">
                    <p class="cta-text">
                        <strong>⚠️ Ação Necessária:</strong> <br> Caso tenha documentos vencidos, alertar ao fornecedor.
                    </p>
                </div>
            </div>
            
            <div class="footer">
                <p class="footer-text">
                    Se você não esperava por este e-mail, favor desconsiderar esta mensagem.
                </p>
                <p class="company-info">
                    Sistema Engeman - Gestão de Fornecedores<br>
                    Este é um e-mail automático, não responda.
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    try:
        msg = Message(
            f'DOCUMENTAÇÕES RECEBIDAS - {fornecedor_nome}', 
            recipients=[destinatario],  
            html=corpo, 
            sender=app.config['MAIL_DEFAULT_SENDER'] 
        )

        if arquivos_paths:
            for arquivo_path in arquivos_paths:
                with app.open_resource(arquivo_path) as fp:
                    msg.attach(arquivo_path, "application/octet-stream", fp.read())

        mail.send(msg)
        print(f'E-mail enviado para {destinatario}')
    
    except Exception as e:
        print(f"Erro ao enviar e-mail para {destinatario}: {e}")
        return None


def enviar_email(destinatario, assunto, corpo, imagem_path):
    try:
        msg = Message(assunto, recipients=[destinatario], html=corpo)

        with open(imagem_path, "rb") as img:
            img_data = img.read()
            encoded_img = base64.b64encode(img_data).decode('utf-8')

        corpo_com_imagem = corpo.replace("cid:engeman_logo", f"data:image/png;base64,{encoded_img}")
        msg.html = corpo_com_imagem

        mail.send(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        raise e



def gerar_token_recuperacao():
    return random.randint(100000, 999999)  


if __name__ == '__main__':
    app.run(debug=True)
