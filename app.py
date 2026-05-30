from flask import Flask, request, jsonify
import mysql.connector
from datetime import date

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',
    'database': 'your_database',
    'user': 'your_username',
    'password': 'your_password'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

class setores_loc:
    def __init__(self, nome_setor, bloco_pavimento, id_setor=None):
        self.id_setor = id_setor
        self.nome_setor = nome_setor
        self.bloco_pavimento = bloco_pavimento

class extintores:
    def __init__(self, numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localizacao_detalhada, id_brigadista_responsavel, validade_carga, data_aquisicao, data_ultima_recarga, status, id=None):
        self.id = id
        self.numero_patrimonio = numero_patrimonio
        self.id_setor = id_setor
        self.codigo_lacre = codigo_lacre
        self.tipo_agente = tipo_agente
        self.classe_incendio = classe_incendio
        self.localizacao_detalhada = localizacao_detalhada
        self.id_brigadista_responsavel = id_brigadista_responsavel
        self.validade_carga = validade_carga
        #self.data_aquisicao = data_aquisicao
        #self.data_ultima_recarga = data_ultima_recarga
        #self.status = status

class inspecoes_extintores:
    def __init__(self, numero_patrimonio, data_inspecao, status_manometro, status_carga, status_agente_disparo, lacre_rompido, validade_teste_nivel1, validade_teste_nivel2, validade_teste_nivel3, integridade_visual, arquivo_evidencia_imagem_path, id_inspecao=None):
        self.id_inspecao = id_inspecao
        self.numero_patrimonio = numero_patrimonio
        self.data_inspecao = data_inspecao
        self.status_manometro = status_manometro
        #self.status_carga = status_carga
        self.status_agente_disparo = status_agente_disparo
        self.lacre_rompido = lacre_rompido
        self.validade_teste_nivel1 = validade_teste_nivel1
        self.validade_teste_nivel2 = validade_teste_nivel2
        self.validade_teste_nivel3 = validade_teste_nivel3
        self.integridade_visual = integridade_visual
        self.arquivo_evidencia_imagem_path = arquivo_evidencia_imagem_path

@app.route('/api/extintor', methods=['POST'])
def cadastrar_extintor():
    dados = request.get_json()
    
    func = extintores(
        dados['numero_patrimonio'],
        dados['id_setor'],
        dados['codigo_lacre'],
        dados['tipo_agente'],
        dados['classe_incendio'],
        dados['localizacao_detalhada'],
        dados['id_brigadista_responsavel'],
        dados['validade_carga'])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "INSERT INTO extintores (numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio, localização_detalhada, id_brigadista_responsavel, validade_carga) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,)"
    
    cursor.execute(sql, (func.numero_patrimonio, func.id_setor, func.codigo_lacre, func.tipo_agente, func.classe_incendio, func.localizacao_detalhada, func.localizacao_detalhada, func.id_brigadista_responsavel, func.validade_carga)
    
    cursor.close()
    conn.close()
    return jsonify({"mensagem": "Extintor cadastrado."}), 201