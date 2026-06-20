from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import mysql.connector
import os
from datetime import date

load_dotenv()

app = Flask(__name__)

#Twilio

twilio_client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

twilio_client.messages.create(
    body="Teste de envio",
    from_=os.getenv("TWILIO_PHONE"),
    to="+55SEUNUMERO"
)

twilio_client.messages.create(
    body="Seu extintor está próximo do vencimento.",
    from_=os.getenv("TWILIO_WHATSAPP"),
    to="whatsapp:+55SEUNUMERO"
)

# Conectar com o Banco de Dados
db_config = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

#Funções Twilio
def enviar_sms(destinatario, mensagem):
    twilio_client.messages.create(
        body=mensagem,
        from_=os.getenv("TWILIO_PHONE"),
        to=destinatario
    )

def enviar_whatsapp(numero, mensagem):
    twilio_client.messages.create(
        body=mensagem,
        from_=os.getenv("TWILIO_WHATSAPP"),
        to=f"whatsapp:{numero}"
    )

 #Funções para fazer o CRUD sem ter que repetir a mesma coisa mil vezes
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
        self.id_setor = id_setor #FK para setores_loc


class extintores:
    def __init__(self, numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localizacao_detalhada, validade_carga, data_aquisicao, data_ultima_recarga, extintor_status):
        self.numero_patrimonio = numero_patrimonio
        self.id_setor = id_setor #FK para setores_loc
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
        self.numero_patrimonio = numero_patrimonio #FK extintores
        self.data_inspecao = data_inspecao
        self.status_manometro = status_manometro
        self.status_carga = status_carga # Adicionar no Sql
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

#==================Setores====================================== 

    #Cadastrar os setores
@app.route('/api/setores', methods=['POST'])
def cadastrar_setor():

    dados = request.get_json()

    executar_sql(
        """
        INSERT INTO setores_loc
        (nome_setor, bloco_pavimento)
        VALUES (%s, %s)
        """,
        (
            dados['nome_setor'],
            dados['bloco_pavimento']
        )
    )

    return jsonify({"mensagem": "Setor cadastrado"})

    #Listar todos os setores
@app.route('/api/setores', methods=['GET'])
def listar_setores():

    resultado = consultar_todos_sql("SELECT * FROM setores_loc")

    return jsonify(resultado)

    #listar um setor
@app.route('/api/setores/<int:id_setor>', methods=['GET'])
def listar_setor(id_setor):

    resultado = consultar_um_sql("SELECT * FROM setores_loc WHERE id_setor = %s", (id_setor,))

    if resultado:
        return jsonify(resultado)
    else:
        return jsonify({"mensagem": "Setor não encontrado"}), 404

    #Atualizar um setor
@app.route('/api/setores/<int:id_setor>', methods=['PUT'])
def atualizar_setor(id_setor):

    dados = request.get_json()

    executar_sql(
        """
        UPDATE setores_loc
        SET nome_setor = %s, bloco_pavimento = %s
        WHERE id_setor = %s
        """,
        (
            dados['nome_setor'],
            dados['bloco_pavimento'],
            id_setor
        )
    )

    return jsonify({"mensagem": "Brigadista atualizado"})

    #Deletar um setor
@app.route('/api/setores/<int:id_setor>', methods=['DELETE'])
def deletar_setor(id_setor):

    executar_sql("DELETE FROM setores_loc WHERE id_setor = %s", (id_setor,))

    return jsonify({"mensagem": "Setor deletado"})

#==================Brigadistas=====================================

    #Cadastrar os Brigadistas
@app.route('/api/brigadistas', methods=['POST'])
def cadastrar_brigadistas():
    
    dados = request.get_json()
    
    executar_sql(
        """
        INSERT INTO brigadistas
        (nome_brigadista, cpf, telefone, email, whatsapp, data_treinamento, id_setor)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
        dados['nome_brigadista'],
        dados['cpf'],
        dados['telefone'],
        dados['email'],
        dados['whatsapp'],
        dados['data_treinamento'],
        dados['id_setor']
        )
    )

    return jsonify({"mensagem": "Brigadista cadastrado"})

    #Listar todos os Brigadistas
@app.route('/api/brigadistas', methods=['GET'])
def listar_brigadistas():

    resultado = consultar_todos_sql("SELECT * FROM brigadistas")

    return jsonify(resultado)

    #Listar um Brigadista
@app.route('/api/brigadistas/<int:id_brigadista>', methods=['GET'])
def listar_brigadista(id_brigadista):
    resultado = consultar_um_sql("SELECT * FROM brigadistas WHERE id_brigadista = %s", (id_brigadista,))

    if resultado:
        return jsonify(resultado)
    else:
        return jsonify({"mensagem": "Brigadista não encontrado"}), 404

    #Atualizar um brigadista
@app.route('/api/brigadistas/<int:id_brigadista>', methods=['PUT'])
def atualizar_brigadista(id_brigadista):

    dados = request.get_json()

    executar_sql(
        """
        UPDATE brigadistas
        SET nome_brigadista = %s, cpf = %s, telefone = %s, email = %s, whatsapp = %s, data_treinamento = %s, id_setor = %s
        WHERE id_brigadista = %s
        """,
        (
            dados["nome_brigadista"],
            dados["cpf"],
            dados["telefone"],
            dados["email"],
            dados["whatsapp"],
            dados["data_treinamento"],
            dados["id_setor"],
            id_brigadista
        )
    )
    
    return jsonify({"mensagem": "Setor atualizado"})

    #Deletar um brigadista
@app.route('/api/brigadistas/<int:id_brigadista>', methods=['DELETE'])
def deletar_brigadista(id_brigadista):

    executar_sql("DELETE FROM brigadistas WHERE id_brigadista = %s", (id_brigadista,))

    return jsonify({"mensagem": "Brigadista deletado"})

#==================Extintores======================================

    #Cadastrar os extintores
@app.route('/api/extintores', methods=['POST'])
def cadastrar_extintor():

    dados = request.get_json()

    executar_sql(
        """
        INSERT INTO extintores
        (numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localizacao_detalhada, validade_carga, data_aquisicao, data_ultima_recarga, extintor_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            dados['numero_patrimonio'],
            dados['id_setor'],
            dados['codigo_lacre'],
            dados['tipo_agente'],
            dados['classe_incendio'],
            dados['localizacao_detalhada'],
            dados['validade_carga'],
            dados['data_aquisicao'],
            dados['data_ultima_recarga'],
            dados['extintor_status']
        )
    )

    return jsonify({"mensagem": "Extintor cadastrado."})

    #Listar todos os extintores
@app.route('/api/extintores', methods=['GET'])
def listar_extintores():

    resultado = consultar_todos_sql("SELECT * FROM extintores")

    return jsonify(resultado)

    #Listar um extintor
@app.route('/api/extintores/<string:numero_patrimonio>', methods=['GET'])
def listar_extintor(numero_patrimonio):

    resultado = consultar_um_sql("SELECT * FROM extintores WHERE numero_patrimonio = %s", (numero_patrimonio,))

    if resultado:
        return jsonify(resultado)
    else:
        return jsonify({"mensagem": "Extintor não encontrado."}), 404
    
    #Atualizar um extintor
@app.route('/api/extintores/<string:numero_patrimonio>', methods=['PUT'])
def atualizar_extintor(numero_patrimonio):

    dados = request.get_json()

    executar_sql(
        """
        UPDATE extintores
        SET id_setor = %s, codigo_lacre = %s, tipo_agente = %s, classe_incendio = %s, localizacao_detalhada = %s, validade_carga = %s, data_aquisicao = %s, data_ultima_recarga = %s, extintor_status = %s
        WHERE numero_patrimonio = %s
        """,
        (
            dados['id_setor'],
            dados['codigo_lacre'],
            dados['tipo_agente'],
            dados['classe_incendio'],
            dados['localizacao_detalhada'],
            dados['validade_carga'],
            dados['data_aquisicao'], #
            dados['data_ultima_recarga'], #
            dados['extintor_status'], #
            numero_patrimonio
        )
    )

    return jsonify({"mensagem": "Extintor atualizado."})

    #Deletar um extintor
@app.route('/api/extintores/<string:numero_patrimonio>', methods=['DELETE'])
def deletar_extintor(numero_patrimonio):

    executar_sql("DELETE FROM extintores WHERE numero_patrimonio = %s", (numero_patrimonio,))

    return jsonify({"mensagem": "Extintor deletado."})

#==================Inspeções======================================

    #Cadastrar uma inspeção
@app.route('/api/inspecoes', methods=['POST'])
def cadastrar_inspecao():

    dados = request.get_json()

    executar_sql(
        """
        INSERT INTO inspecoes_extintores
        (id_brigadista, numero_patrimonio, data_inspecao, status_manometro, status_carga, status_agente_disparo, lacre_rompido, data_teste_nivel1, data_teste_nivel2, data_teste_nivel3, data_vencimento_nivel1, data_vencimento_nivel2, data_vencimento_nivel3, integridade_visual, arquivo_evidencia_imagem_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            dados['id_brigadista'],
            dados['numero_patrimonio'],
            dados['data_inspecao'],
            dados['status_manometro'],
            dados['status_carga'], #
            dados['status_agente_disparo'],
            dados['lacre_rompido'],
            dados['data_teste_nivel1'],
            dados['data_teste_nivel2'],
            dados['data_teste_nivel3'],
            dados['data_vencimento_nivel1'],
            dados['data_vencimento_nivel2'],
            dados['data_vencimento_nivel3'],
            dados['integridade_visual'],
            dados['arquivo_evidencia_imagem_path']
        )
    )

    return jsonify({"mensagem": "Inspeção cadastrada."})

    #Listar todas as inspeções
@app.route('/api/inspecoes', methods=['GET'])
def listar_inspecoes():

    resultado = consultar_todos_sql("SELECT * FROM inspecoes_extintores")

    return jsonify(resultado)

    #Listar todas as inspeções de um extintor específico
@app.route('/api/inspecoes/A/<string:numero_patrimonio>', methods=['GET'])
def listar_inspecao(numero_patrimonio):

    resultado = consultar_um_sql("SELECT * FROM inspecoes_extintores WHERE numero_patrimonio = %s", (numero_patrimonio,))

    if resultado:
        return jsonify(resultado)
    else:
        return jsonify({"mensagem": "Inspeção não encontrada."}), 404
    

    #Listar inspeção com o brigadista
@app.route('/api/inspecoes/B/<int:id_brigadista>', methods=['GET'])
def listar_inspecao_brigadista(id_brigadista):

    resultado = consultar_um_sql("SELECT i.*, b.nome_brigadista FROM inspecoes_extintores i JOIN brigadistas b ON i.id_brigadista = b.id_brigadista WHERE i.id_brigadista = %s", (id_brigadista,))

    if resultado:
        return jsonify(resultado)
    else:
        return jsonify({"mensagem": "Inspeção não encontrada."}), 404

    #Atualizar uma inspeção
@app.route('/api/inspecoes/<int:id_inspecao>', methods=['PUT'])
def atualizar_inspecao(id_inspecao):

    dados = request.get_json()

    executar_sql(
        """
        UPDATE inspecoes_extintores
        SET id_brigadista = %s, numero_patrimonio = %s, data_inspecao = %s, status_manometro = %s, status_carga = %s, status_agente_disparo = %s, lacre_rompido = %s, data_teste_nivel1 = %s, data_teste_nivel2 = %s, data_teste_nivel3 = %s, data_vencimento_nivel1 = %s,
        data_vencimento_nivel2 = %s, data_vencimento_nivel3 = %s, integridade_visual = %s, arquivo_evidencia_imagem_path = %s
        WHERE id_inspecao = %s
        """,
        (
            dados['id_brigadista'],
            dados['numero_patrimonio'],
            dados['data_inspecao'],
            dados['status_manometro'],
            dados['status_carga'],
            dados['status_agente_disparo'],
            dados['lacre_rompido'],
            dados['data_teste_nivel1'],
            dados['data_teste_nivel2'],
            dados['data_teste_nivel3'],
            dados['data_vencimento_nivel1'],
            dados['data_vencimento_nivel2'],
            dados['data_vencimento_nivel3'],
            dados['integridade_visual'],
            dados['arquivo_evidencia_imagem_path'],
            id_inspecao
        )
    )

    return jsonify({"mensagem": "Inspeção atualizada."})

    #Deletar uma inspeção
@app.route('/api/inspecoes/<int:id_inspecao>', methods=['DELETE'])
def deletar_inspecao(id_inspecao):

    executar_sql("DELETE FROM inspecoes_extintores WHERE id_inspecao = %s", (id_inspecao,))

    return jsonify({"mensagem": "Inspeção deletada."})

if __name__ == '__main__':
    # Precisa disso aqui pra fazer o debug
    app.run(host='127.0.0.1', port=5000, debug=True)

#Teste
"""enviar_whatsapp(
    "+5531999999999",
    "Seu extintor vence em 30 dias."
)"""

"""
mensagem = (
    f"Olá! O extintor patrimônio {patrimonio} "
    f"vence em {dias} dias. Manutenção necessária."
)

enviar_whatsapp(brigadista["telefone"], mensagem)"""