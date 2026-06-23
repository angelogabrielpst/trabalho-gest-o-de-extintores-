from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import mysql.connector
import os
import re
from datetime import date

load_dotenv()

app = Flask(__name__)

# Configuração do Cliente Twilio
twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

# Conectar com o Banco de Dados
def get_db_connection():
    host_banco = os.getenv('DB_HOST') or '127.0.0.1'
    if host_banco == '.':
        host_banco = '127.0.0.1'

    db_config = {
        'host': host_banco,
        'user': os.getenv('DB_USER') or 'root',
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_DATABASE'),
        'port': int(os.getenv('DB_PORT') or 3306)
    }

    return mysql.connector.connect(**db_config)

# ==========================================================
# FUNÇÕES AUXILIARES TWILIO
# ==========================================================
def formatar_para_twilio(telefone_raw):
    if not telefone_raw:
        return ""
    # Remove parênteses, traços, espaços e mantém apenas números
    numeros = re.sub(r'\D', '', str(telefone_raw))
    if len(numeros) == 11:
        return f"+55{numeros}"
    elif len(numeros) == 13:
        return f"+{numeros}"
    return numeros

def enviar_sms(tel_formatado, mensagem):
    if tel_formatado:
        twilio_client.messages.create(
            body=mensagem,
            from_=os.getenv("TWILIO_PHONE_NUMBER"),
            to=tel_formatado
        )

def enviar_whatsapp(tel_formatado, mensagem):
    if tel_formatado:
        twilio_client.messages.create(
            body=mensagem,
            from_=f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
            to=f"whatsapp:{tel_formatado}"
        )

# Funções pro SQl
def executar_sql(sql, parametros=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, parametros)
    conn.commit()
    cursor.close()
    conn.close()

def consultar_todos_sql(sql, parametros=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, parametros)
    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados

def consultar_um_sql(sql, parametros=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, parametros)
    resultado = cursor.fetchone()
    cursor.close()
    conn.close()
    return resultado

# Classes
class setores_loc:
    def __init__(self, nome_setor, bloco_pavimento, id_setor=None):
        self.id_setor = id_setor
        self.nome_setor = nome_setor
        self.bloco_pavimento = bloco_pavimento

class brigadistas:
    def __init__(self, nome_brigadista, cpf, telefone, email, whatsapp, data_treinamento, id_setor, id_brigadista=None):
        self.id_brigadista = id_brigadista
        self.nome_brigadista = nome_brigadista
        self.cpf = cpf
        self.telefone = telefone
        self.email = email
        self.whatsapp = whatsapp
        self.data_treinamento = data_treinamento
        self.id_setor = id_setor

class extintores:
    def __init__(self, numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localizacao_detalhada, validade_carga, data_aquisicao, data_ultima_recarga, extintor_status):
        self.numero_patrimonio = numero_patrimonio
        self.id_setor = id_setor
        self.codigo_lacre = codigo_lacre
        self.tipo_agente = tipo_agente
        self.classe_incendio = classe_incendio
        self.localizacao_detalhada = localizacao_detalhada
        self.validade_carga = validade_carga
        self.data_aquisicao = data_aquisicao
        self.data_ultima_recarga = data_ultima_recarga
        self.extintor_status = extintor_status

class inspecoes_extintores:
    def __init__(self, numero_patrimonio, data_inspecao, status_manometro, status_carga, status_agente_disparo, lacre_rompido, data_teste_nivel1, data_teste_nivel2, data_teste_nivel3, data_vencimento_nivel1, data_vencimento_nivel2, data_vencimento_nivel3, integridade_visual, arquivo_evidencia_imagem_path, id_inspecao=None):
        self.id_inspecao = id_inspecao
        self.numero_patrimonio = numero_patrimonio
        self.data_inspecao = data_inspecao
        self.status_manometro = status_manometro
        self.status_carga = status_carga
        self.status_agente_disparo = status_agente_disparo
        self.lacre_rompido = lacre_rompido
        self.data_teste_nivel1 = data_teste_nivel1
        self.data_teste_nivel2 = data_teste_nivel2
        self.data_teste_nivel3 = data_teste_nivel3
        self.data_vencimento_nivel1 = data_vencimento_nivel1
        self.data_vencimento_nivel2 = data_vencimento_nivel2
        self.data_vencimento_nivel3 = data_vencimento_nivel3
        self.integridade_visual = integridade_visual
        self.arquivo_evidencia_imagem_path = arquivo_evidencia_imagem_path

# ==========================================================
# ROTAS: SETORES
# ==========================================================

@app.route('/api/setores', methods=['POST'])
def cadastrar_setor():
    dados = request.get_json()
    executar_sql(
        "INSERT INTO setores_loc (nome_setor, bloco_pavimento) VALUES (%s, %s)",
        (dados['nome_setor'], dados['bloco_pavimento'])
    )
    return jsonify({"mensagem": "Setor cadastrado"})

@app.route('/api/setores', methods=['GET'])
def listar_setores():
    resultado = consultar_todos_sql("SELECT * FROM setores_loc")
    return jsonify(resultado)

@app.route('/api/setores/<int:id_setor>', methods=['GET'])
def listar_setor(id_setor):
    resultado = consultar_um_sql("SELECT * FROM setores_loc WHERE id_setor = %s", (id_setor,))
    if resultado:
        return jsonify(resultado)
    return jsonify({"mensagem": "Setor não encontrado"}), 404

@app.route('/api/setores/<int:id_setor>', methods=['PUT'])
def atualizar_setor(id_setor):
    dados = request.get_json()
    executar_sql(
        "UPDATE setores_loc SET nome_setor = %s, bloco_pavimento = %s WHERE id_setor = %s",
        (dados['nome_setor'], dados['bloco_pavimento'], id_setor)
    )
    return jsonify({"mensagem": "Setor atualizado"})

@app.route('/api/setores/<int:id_setor>', methods=['DELETE'])
def deletar_setor(id_setor):
    executar_sql("DELETE FROM setores_loc WHERE id_setor = %s", (id_setor,))
    return jsonify({"mensagem": "Setor deletado"})

# ==========================================================
# ROTAS: BRIGADISTAS
# ==========================================================

@app.route('/api/brigadistas', methods=['POST'])
def cadastrar_brigadistas():
    dados = request.get_json()
    executar_sql(
        """
        INSERT INTO brigadistas (nome_brigadista, cpf, telefone, email, whatsapp, data_treinamento, id_setor)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (dados['nome_brigadista'], dados['cpf'], dados['telefone'], dados['email'], dados['whatsapp'], dados['data_treinamento'], dados['id_setor'])
    )
    return jsonify({"mensagem": "Brigadista cadastrado"})

@app.route('/api/brigadistas', methods=['GET'])
def listar_brigadistas():
    resultado = consultar_todos_sql("SELECT * FROM brigadistas")
    return jsonify(resultado)

@app.route('/api/brigadistas/<int:id_brigadista>', methods=['GET'])
def listar_brigadista(id_brigadista):
    resultado = consultar_um_sql("SELECT * FROM brigadistas WHERE id_brigadista = %s", (id_brigadista,))
    if resultado:
        return jsonify(resultado)
    return jsonify({"mensagem": "Brigadista não encontrado"}), 404

@app.route('/api/brigadistas/<int:id_brigadista>', methods=['PUT'])
def atualizar_brigadista(id_brigadista):
    dados = request.get_json()
    executar_sql(
        """
        UPDATE brigadistas SET nome_brigadista = %s, cpf = %s, telefone = %s, email = %s, whatsapp = %s, data_treinamento = %s, id_setor = %s
        WHERE id_brigadista = %s
        """,
        (dados["nome_brigadista"], dados["cpf"], dados["telefone"], dados["email"], dados["whatsapp"], dados["data_treinamento"], dados["id_setor"], id_brigadista)
    )
    return jsonify({"mensagem": "Brigadista atualizado"})

@app.route('/api/brigadistas/<int:id_brigadista>', methods=['DELETE'])
def deletar_brigadista(id_brigadista):
    executar_sql("DELETE FROM brigadistas WHERE id_brigadista = %s", (id_brigadista,))
    return jsonify({"mensagem": "Brigadista deletado"})

# ==========================================================
# ROTAS: EXTINTORES
# ==========================================================

@app.route('/api/extintores', methods=['POST'])
def cadastrar_extintor():
    dados = request.get_json()
    executar_sql(
        """
        INSERT INTO extintores (numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localizacao_detalhada, validade_carga, data_aquisicao, data_ultima_recarga, extintor_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (dados['numero_patrimonio'], dados['id_setor'], dados['codigo_lacre'], dados['tipo_agente'], dados['classe_incendio'], dados['localizacao_detalhada'], dados['validade_carga'], dados['data_aquisicao'], dados['data_ultima_recarga'], dados['extintor_status'])
    )
    return jsonify({"mensagem": "Extintor cadastrado."})

@app.route('/api/extintores', methods=['GET'])
def listar_extintores():
    resultado = consultar_todos_sql("SELECT * FROM extintores")
    return jsonify(resultado)

@app.route('/api/extintores/<string:numero_patrimonio>', methods=['GET'])
def listar_extintor(numero_patrimonio):
    resultado = consultar_um_sql("SELECT * FROM extintores WHERE numero_patrimonio = %s", (numero_patrimonio,))
    if resultado:
        return jsonify(resultado)
    return jsonify({"mensagem": "Extintor não encontrado."}), 404

@app.route('/api/extintores/<string:numero_patrimonio>', methods=['PUT'])
def atualizar_extintor(numero_patrimonio):
    dados = request.get_json()
    executar_sql(
        """
        UPDATE extintores SET id_setor = %s, codigo_lacre = %s, tipo_agente = %s, classe_incendio = %s, localizacao_detalhada = %s, validade_carga = %s, data_aquisicao = %s, data_ultima_recarga = %s, extintor_status = %s
        WHERE numero_patrimonio = %s
        """,
        (dados['id_setor'], dados['codigo_lacre'], dados['tipo_agente'], dados['classe_incendio'], dados['localizacao_detalhada'], dados['validade_carga'], dados['data_aquisicao'], dados['data_ultima_recarga'], dados['extintor_status'], numero_patrimonio)
    )
    return jsonify({"mensagem": "Extintor updated."})

@app.route('/api/extintores/<string:numero_patrimonio>', methods=['DELETE'])
def deletar_extintor(numero_patrimonio):
    executar_sql("DELETE FROM extintores WHERE numero_patrimonio = %s", (numero_patrimonio,))
    return jsonify({"mensagem": "Extintor deletado."})

# ==========================================================
# ROTAS: INSPEÇÕES
# ==========================================================

@app.route('/api/inspecoes', methods=['POST'])
def cadastrar_inspecao():
    dados = request.get_json()
    executar_sql(
        """
        INSERT INTO inspecoes_extintores (id_brigadista, numero_patrimonio, data_inspecao, status_manometro, status_carga, status_agente_disparo, lacre_rompido, data_teste_nivel1, data_teste_nivel2, data_teste_nivel3, data_vencimento_nivel1, data_vencimento_nivel2, data_vencimento_nivel3, integridade_visual, arquivo_evidencia_imagem_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (dados['id_brigadista'], dados['numero_patrimonio'], dados['data_inspecao'], dados['status_manometro'], dados['status_carga'], dados['status_agente_disparo'], dados['lacre_rompido'], dados['data_teste_nivel1'], dados['data_teste_nivel2'], dados['data_teste_nivel3'], dados['data_vencimento_nivel1'], dados['data_vencimento_nivel2'], dados['data_vencimento_nivel3'], dados['integridade_visual'], dados['arquivo_evidencia_imagem_path'])
    )
    return jsonify({"mensagem": "Inspeção cadastrada."})

@app.route('/api/inspecoes', methods=['GET'])
def listar_inspecoes():
    resultado = consultar_todos_sql("SELECT * FROM inspecoes_extintores")
    return jsonify(resultado)

@app.route('/api/inspecoes/A/<string:numero_patrimonio>', methods=['GET'])
def listar_inspecao(numero_patrimonio):
    resultado = consultar_um_sql(
        "SELECT * FROM inspecoes_extintores WHERE numero_patrimonio = %s",
        (numero_patrimonio,)
    )
    if resultado:
        return jsonify(resultado), 200
    return jsonify({"mensagem": "Inspeção não encontrada."}), 404

@app.route('/api/inspecoes/B/<int:id_brigadista>', methods=['GET'])
def listar_inspecao_brigadista(id_brigadista):
    resultados = consultar_todos_sql(
        "SELECT i.*, b.nome_brigadista FROM inspecoes_extintores i "
        "JOIN brigadistas b ON i.id_brigadista = b.id_brigadista "
        "WHERE i.id_brigadista = %s", 
        (id_brigadista,)
    )
    if resultados:
        return jsonify(resultados), 200
    return jsonify({"mensagem": "Nenhuma inspeção encontrada para este brigadista."}), 404

@app.route('/api/inspecoes/<int:id_inspecao>', methods=['PUT'])
def atualizar_inspecao(id_inspecao):
    dados = request.get_json()
    executar_sql(
        """
        UPDATE inspecoes_extintores SET id_brigadista = %s, numero_patrimonio = %s, data_inspecao = %s, status_manometro = %s, status_carga = %s, status_agente_disparo = %s, lacre_rompido = %s, data_teste_nivel1 = %s, data_teste_nivel2 = %s, data_teste_nivel3 = %s, data_vencimento_nivel1 = %s, data_vencimento_nivel2 = %s, data_vencimento_nivel3 = %s, integridade_visual = %s, arquivo_evidencia_imagem_path = %s
        WHERE id_inspecao = %s
        """,
        (dados['id_brigadista'], dados['numero_patrimonio'], dados['data_inspecao'], dados['status_manometro'], dados['status_carga'], dados['status_agente_disparo'], dados['lacre_rompido'], dados['data_teste_nivel1'], dados['data_teste_nivel2'], dados['data_teste_nivel3'], dados['data_vencimento_nivel1'], dados['data_vencimento_nivel2'], dados['data_vencimento_nivel3'], dados['integridade_visual'], dados['arquivo_evidencia_imagem_path'], id_inspecao)
    )
    return jsonify({"mensagem": "Inspeção atualizada."})

@app.route('/api/inspecoes/<int:id_inspecao>', methods=['DELETE'])
def deletar_inspecao(id_inspecao):
    executar_sql("DELETE FROM inspecoes_extintores WHERE id_inspecao = %s", (id_inspecao,))
    return jsonify({"mensagem": "Inspeção deletada."})

# ==========================================================
# ROTA AUTOMATIZADA: DISPARO DE NOTIFICAÇÕES EM LOTE
# ==========================================================
@app.route('/api/notificar-extintores-vencendo', methods=['POST'])
def notificar_extintores_vencendo():
    try:
        sql = """
            SELECT e.numero_patrimonio, e.tipo_agente, e.validade_carga, s.nome_setor, s.bloco_pavimento, b.nome_brigadista, b.telefone, b.whatsapp
            FROM extintores e
            JOIN setores_loc s ON e.id_setor = s.id_setor
            JOIN brigadistas b ON s.id_setor = b.id_setor
            WHERE e.validade_carga BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        """
        expirando = consultar_todos_sql(sql)

        contador = 0
        for reg in expirando:
            tel_sms = formatar_para_twilio(reg['telefone'])
            tel_wa = formatar_para_twilio(reg['whatsapp'])

            # Validação defensiva (Evita o erro de requisição Twilio 21604)
            if (not tel_sms or len(tel_sms) < 12) and (not tel_wa or len(tel_wa) < 12):
                print(f"Aviso: Registro do brigadista {reg['nome_brigadista']} ignorado por falta de números válidos.")
                continue

            mensagem = (
                f"Ola {reg['nome_brigadista']}! O extintor de {reg['tipo_agente']} "
                f"(Patrimonio: {reg['numero_patrimonio']}) localizado no setor {reg['nome_setor']} "
                f"({reg['bloco_pavimento']}) vai vencer em breve na data: {reg['validade_carga']}. "
                f"Por favor, providencie a recarga."
            )

            if tel_sms and len(tel_sms) >= 12:
                enviar_sms(tel_sms, mensagem)

            # CORRIGIDO: Parâmetros alinhados com a definição da função enviar_whatsapp
            if tel_wa and len(tel_wa) >= 12:
                enviar_whatsapp(tel_wa, mensagem)

            contador += 1

        return jsonify({
            "mensagem": f"Sucesso! {contador} alertas de extintores a vencer foram enviados aos brigadistas dos setores responsáveis."
        }), 200

    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
