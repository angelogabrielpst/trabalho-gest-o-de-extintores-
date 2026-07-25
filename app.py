from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error as MySQLError
import os
import re
from datetime import date, datetime

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:
    Client = None
    TwilioRestException = Exception

load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# ==========================================================
# CONFIGURAÇÃO
# ==========================================================

def criar_cliente_twilio():
    """Cria o cliente da Twilio apenas se as variáveis estiverem configuradas."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token or Client is None:
        return None

    return Client(account_sid, auth_token)

client = criar_cliente_twilio()


@app.after_request
def aplicar_cors(response):
    """Permite testar o frontend pelo navegador sem erro de CORS."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
    return response


@app.route("/")
def pagina_inicial():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "mensagem": "API SST Extintores funcionando"
    })


# ==========================================================
# BANCO DE DADOS
# ==========================================================

def get_db_connection():
    host_banco = os.getenv("DB_HOST") or "127.0.0.1"
    if host_banco == ".":
        host_banco = "127.0.0.1"

    db_config = {
        "host": host_banco,
        "user": os.getenv("DB_USER") or "root",
        "password": os.getenv("DB_PASSWORD") or "",
        "database": os.getenv("DB_DATABASE") or "sst_extintores_db",
        "port": int(os.getenv("DB_PORT") or 3306)
    }

    return mysql.connector.connect(**db_config)


def converter_datas(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def normalizar_registro(registro):
    if registro is None:
        return None

    return {chave: converter_datas(valor) for chave, valor in registro.items()}


def normalizar_lista(registros):
    return [normalizar_registro(registro) for registro in registros]


def executar_sql(sql, parametros=None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        conn.commit()

        return {
            "rowcount": cursor.rowcount,
            "lastrowid": cursor.lastrowid
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def consultar_todos_sql(sql, parametros=None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        resultados = cursor.fetchall()
        return normalizar_lista(resultados)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def consultar_um_sql(sql, parametros=None):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, parametros)
        resultado = cursor.fetchone()
        return normalizar_registro(resultado)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.errorhandler(MySQLError)
def tratar_erro_mysql(erro):
    return jsonify({
        "erro": "Erro no banco de dados",
        "detalhes": str(erro)
    }), 400


@app.errorhandler(KeyError)
def tratar_campo_faltando(erro):
    return jsonify({
        "erro": "Campo obrigatório não enviado",
        "campo": str(erro).replace("'", "")
    }), 400


@app.errorhandler(404)
def tratar_404(_):
    return jsonify({"erro": "Rota não encontrada"}), 404


def normalizar_datetime(valor):
    """Converte datetime-local do HTML para formato aceito pelo MySQL."""
    if not valor:
        return valor

    valor = str(valor).replace("T", " ")
    if re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", valor):
        valor += ":00"

    return valor


# ==========================================================
# FUNÇÕES AUXILIARES TWILIO
# ==========================================================

def formatar_para_twilio(telefone_raw):
    if not telefone_raw:
        return ""

    numeros = re.sub(r"\D", "", str(telefone_raw))

    if len(numeros) == 11:
        return f"+55{numeros}"

    if len(numeros) == 13:
        return f"+{numeros}"

    if len(numeros) > 11 and not numeros.startswith("55"):
        return f"+{numeros}"

    return numeros


def enviar_whatsapp(tel_formatado, mensagem):
    if client is None:
        return {
            "enviado": False,
            "mensagem": "Twilio não configurado. Configure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN e TWILIO_WHATSAPP_NUMBER no .env."
        }

    if not tel_formatado:
        return {
            "enviado": False,
            "mensagem": "Telefone inválido"
        }

    numero_limpo = "".join(filter(str.isdigit, tel_formatado))

    if len(numero_limpo) <= 11:
        numero_limpo = f"55{numero_limpo}"

    numero_final = f"+{numero_limpo}"
    numero_origem = os.getenv("TWILIO_WHATSAPP_NUMBER")

    if not numero_origem:
        return {
            "enviado": False,
            "mensagem": "TWILIO_WHATSAPP_NUMBER não configurado no .env."
        }

    try:
        msg = client.messages.create(
            body=mensagem,
            from_=f"whatsapp:{numero_origem}",
            to=f"whatsapp:{numero_final}"
        )
        return {
            "enviado": True,
            "mensagem": f"Mensagem enviada com sucesso. SID: {msg.sid}"
        }
    except TwilioRestException as e:
        return {
            "enviado": False,
            "mensagem": f"Erro da Twilio ({getattr(e, 'code', 'sem código')}): {getattr(e, 'msg', str(e))}"
        }


# ==========================================================
# ROTAS: DASHBOARD
# ==========================================================

@app.route("/api/dashboard", methods=["GET"])
def obter_dashboard():
    total_setores = consultar_um_sql("SELECT COUNT(*) AS total FROM setores_loc")
    total_brigadistas = consultar_um_sql("SELECT COUNT(*) AS total FROM brigadistas")
    total_extintores = consultar_um_sql("SELECT COUNT(*) AS total FROM extintores")
    total_inspecoes = consultar_um_sql("SELECT COUNT(*) AS total FROM inspecoes_extintores")

    vencidos = consultar_um_sql("""
        SELECT COUNT(*) AS total
        FROM extintores
        WHERE validade_carga < CURDATE()
    """)

    vencendo = consultar_um_sql("""
        SELECT COUNT(*) AS total
        FROM extintores
        WHERE validade_carga BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    """)

    ultimas_inspecoes = consultar_todos_sql("""
        SELECT
            i.id_inspecao,
            i.numero_patrimonio,
            i.data_inspecao,
            i.data_vencimento_nivel1,
            b.nome_brigadista,
            e.tipo_agente
        FROM inspecoes_extintores i
        JOIN brigadistas b ON i.id_brigadista = b.id_brigadista
        JOIN extintores e ON i.numero_patrimonio = e.numero_patrimonio
        ORDER BY i.data_inspecao DESC
        LIMIT 5
    """)

    status_extintores = consultar_todos_sql("""
        SELECT extintor_status, COUNT(*) AS total
        FROM extintores
        GROUP BY extintor_status
        ORDER BY total DESC
    """)

    agentes_extintores = consultar_todos_sql("""
        SELECT tipo_agente, COUNT(*) AS total
        FROM extintores
        GROUP BY tipo_agente
        ORDER BY total DESC
    """)

    proximos_vencimentos = consultar_todos_sql("""
        SELECT
            e.numero_patrimonio,
            e.tipo_agente,
            e.validade_carga,
            e.extintor_status,
            e.localizacao_detalhada,
            s.nome_setor,
            DATEDIFF(e.validade_carga, CURDATE()) AS dias_restantes
        FROM extintores e
        JOIN setores_loc s ON e.id_setor = s.id_setor
        WHERE e.validade_carga <= DATE_ADD(CURDATE(), INTERVAL 60 DAY)
        ORDER BY e.validade_carga ASC
        LIMIT 8
    """)

    return jsonify({
        "total_setores": total_setores["total"],
        "total_brigadistas": total_brigadistas["total"],
        "total_extintores": total_extintores["total"],
        "total_inspecoes": total_inspecoes["total"],
        "extintores_vencidos": vencidos["total"],
        "extintores_vencendo_30_dias": vencendo["total"],
        "ultimas_inspecoes": ultimas_inspecoes,
        "status_extintores": status_extintores,
        "agentes_extintores": agentes_extintores,
        "proximos_vencimentos": proximos_vencimentos
    })


# ==========================================================
# ROTAS: SETORES
# ==========================================================

@app.route("/api/setores", methods=["POST"])
def cadastrar_setor():
    dados = request.get_json() or {}

    resultado = executar_sql(
        "INSERT INTO setores_loc (nome_setor, bloco_pavimento) VALUES (%s, %s)",
        (dados["nome_setor"], dados["bloco_pavimento"])
    )

    return jsonify({
        "mensagem": "Setor cadastrado",
        "id_setor": resultado["lastrowid"]
    }), 201


@app.route("/api/setores", methods=["GET"])
def listar_setores():
    resultado = consultar_todos_sql("SELECT * FROM setores_loc ORDER BY nome_setor")
    return jsonify(resultado)


@app.route("/api/setores/<int:id_setor>", methods=["GET"])
def listar_setor(id_setor):
    resultado = consultar_um_sql(
        "SELECT * FROM setores_loc WHERE id_setor = %s",
        (id_setor,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Setor não encontrado"}), 404


@app.route("/api/setores/<int:id_setor>", methods=["PUT"])
def atualizar_setor(id_setor):
    dados = request.get_json() or {}

    resultado = executar_sql(
        "UPDATE setores_loc SET nome_setor = %s, bloco_pavimento = %s WHERE id_setor = %s",
        (dados["nome_setor"], dados["bloco_pavimento"], id_setor)
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Setor não encontrado"}), 404

    return jsonify({"mensagem": "Setor atualizado"})


@app.route("/api/setores/<int:id_setor>", methods=["DELETE"])
def deletar_setor(id_setor):
    resultado = executar_sql(
        "DELETE FROM setores_loc WHERE id_setor = %s",
        (id_setor,)
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Setor não encontrado"}), 404

    return jsonify({"mensagem": "Setor deletado"})


# ==========================================================
# ROTAS: BRIGADISTAS
# ==========================================================

@app.route("/api/brigadistas", methods=["POST"])
def cadastrar_brigadista():
    dados = request.get_json() or {}

    resultado = executar_sql(
        """
        INSERT INTO brigadistas
        (nome_brigadista, cpf, telefone, email, whatsapp, data_treinamento, id_setor)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            dados["nome_brigadista"],
            dados["cpf"],
            dados["telefone"],
            dados.get("email"),
            dados.get("whatsapp"),
            dados.get("data_treinamento") or None,
            dados["id_setor"]
        )
    )

    return jsonify({
        "mensagem": "Brigadista cadastrado",
        "id_brigadista": resultado["lastrowid"]
    }), 201


@app.route("/api/brigadistas", methods=["GET"])
def listar_brigadistas():
    resultado = consultar_todos_sql("""
        SELECT
            b.*,
            s.nome_setor,
            s.bloco_pavimento
        FROM brigadistas b
        JOIN setores_loc s ON b.id_setor = s.id_setor
        ORDER BY b.nome_brigadista
    """)
    return jsonify(resultado)


@app.route("/api/brigadistas/<int:id_brigadista>", methods=["GET"])
def listar_brigadista(id_brigadista):
    resultado = consultar_um_sql(
        "SELECT * FROM brigadistas WHERE id_brigadista = %s",
        (id_brigadista,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Brigadista não encontrado"}), 404


@app.route("/api/brigadistas/<int:id_brigadista>", methods=["PUT"])
def atualizar_brigadista(id_brigadista):
    dados = request.get_json() or {}

    resultado = executar_sql(
        """
        UPDATE brigadistas
        SET nome_brigadista = %s,
            cpf = %s,
            telefone = %s,
            email = %s,
            whatsapp = %s,
            data_treinamento = %s,
            id_setor = %s
        WHERE id_brigadista = %s
        """,
        (
            dados["nome_brigadista"],
            dados["cpf"],
            dados["telefone"],
            dados.get("email"),
            dados.get("whatsapp"),
            dados.get("data_treinamento") or None,
            dados["id_setor"],
            id_brigadista
        )
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Brigadista não encontrado"}), 404

    return jsonify({"mensagem": "Brigadista atualizado"})


@app.route("/api/brigadistas/<int:id_brigadista>", methods=["DELETE"])
def deletar_brigadista(id_brigadista):
    resultado = executar_sql(
        "DELETE FROM brigadistas WHERE id_brigadista = %s",
        (id_brigadista,)
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Brigadista não encontrado"}), 404

    return jsonify({"mensagem": "Brigadista deletado"})


# ==========================================================
# ROTAS: EXTINTORES
# ==========================================================

@app.route("/api/extintores", methods=["POST"])
def cadastrar_extintor():
    dados = request.get_json() or {}

    executar_sql(
        """
        INSERT INTO extintores
        (numero_patrimonio, id_setor, codigo_lacre, tipo_agente, classe_incendio,
         localizacao_detalhada, validade_carga, data_aquisicao, data_ultima_recarga, extintor_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            dados["numero_patrimonio"],
            dados["id_setor"],
            dados["codigo_lacre"],
            dados["tipo_agente"],
            dados["classe_incendio"],
            dados["localizacao_detalhada"],
            dados["validade_carga"],
            dados["data_aquisicao"],
            dados["data_ultima_recarga"],
            dados["extintor_status"]
        )
    )

    return jsonify({"mensagem": "Extintor cadastrado"}), 201


@app.route("/api/extintores", methods=["GET"])
def listar_extintores():
    resultado = consultar_todos_sql("""
        SELECT
            e.*,
            s.nome_setor,
            s.bloco_pavimento
        FROM extintores e
        JOIN setores_loc s ON e.id_setor = s.id_setor
        ORDER BY e.numero_patrimonio
    """)
    return jsonify(resultado)


@app.route("/api/extintores/<string:numero_patrimonio>", methods=["GET"])
def listar_extintor(numero_patrimonio):
    resultado = consultar_um_sql(
        "SELECT * FROM extintores WHERE numero_patrimonio = %s",
        (numero_patrimonio,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Extintor não encontrado"}), 404


@app.route("/api/extintores/<string:numero_patrimonio>", methods=["PUT"])
def atualizar_extintor(numero_patrimonio):
    dados = request.get_json() or {}

    resultado = executar_sql(
        """
        UPDATE extintores
        SET id_setor = %s,
            codigo_lacre = %s,
            tipo_agente = %s,
            classe_incendio = %s,
            localizacao_detalhada = %s,
            validade_carga = %s,
            data_aquisicao = %s,
            data_ultima_recarga = %s,
            extintor_status = %s
        WHERE numero_patrimonio = %s
        """,
        (
            dados["id_setor"],
            dados["codigo_lacre"],
            dados["tipo_agente"],
            dados["classe_incendio"],
            dados["localizacao_detalhada"],
            dados["validade_carga"],
            dados["data_aquisicao"],
            dados["data_ultima_recarga"],
            dados["extintor_status"],
            numero_patrimonio
        )
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Extintor não encontrado"}), 404

    return jsonify({"mensagem": "Extintor atualizado"})


@app.route("/api/extintores/<string:numero_patrimonio>", methods=["DELETE"])
def deletar_extintor(numero_patrimonio):
    resultado = executar_sql(
        
        "DELETE FROM extintores WHERE numero_patrimonio = %s",
        (numero_patrimonio,)
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Extintor não encontrado"}), 404

    return jsonify({"mensagem": "Extintor deletado"})


# ==========================================================
# ROTAS: INSPEÇÕES
# ==========================================================

@app.route("/api/inspecoes", methods=["POST"])
def cadastrar_inspecao():
    dados = request.get_json() or {}

    resultado = executar_sql(
        """
        INSERT INTO inspecoes_extintores
        (id_brigadista, numero_patrimonio, data_inspecao, status_manometro, status_carga,
         status_agente_disparo, lacre_rompido, data_teste_nivel1, data_teste_nivel2,
         data_teste_nivel3, integridade_visual, arquivo_evidencia_imagem_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            dados["id_brigadista"],
            dados["numero_patrimonio"],
            normalizar_datetime(dados["data_inspecao"]),
            dados["status_manometro"],
            dados["status_carga"],
            dados["status_agente_disparo"],
            1 if dados.get("lacre_rompido") else 0,
            dados["data_teste_nivel1"],
            dados["data_teste_nivel2"],
            dados["data_teste_nivel3"],
            dados["integridade_visual"],
            dados.get("arquivo_evidencia_imagem_path") or "sem_arquivo"
        )
    )

    return jsonify({
        "mensagem": "Inspeção cadastrada",
        "id_inspecao": resultado["lastrowid"]
    }), 201


@app.route("/api/inspecoes", methods=["GET"])
def listar_inspecoes():
    resultado = consultar_todos_sql("""
        SELECT
            i.*,
            b.nome_brigadista,
            e.tipo_agente,
            e.localizacao_detalhada
        FROM inspecoes_extintores i
        JOIN brigadistas b ON i.id_brigadista = b.id_brigadista
        JOIN extintores e ON i.numero_patrimonio = e.numero_patrimonio
        ORDER BY i.data_inspecao DESC
    """)
    return jsonify(resultado)


@app.route("/api/inspecoes/<int:id_inspecao>", methods=["GET"])
def listar_inspecao_por_id(id_inspecao):
    resultado = consultar_um_sql(
        "SELECT * FROM inspecoes_extintores WHERE id_inspecao = %s",
        (id_inspecao,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Inspeção não encontrada"}), 404


@app.route("/api/inspecoes/A/<string:numero_patrimonio>", methods=["GET"])
def listar_inspecoes_por_patrimonio(numero_patrimonio):
    resultado = consultar_todos_sql(
        "SELECT * FROM inspecoes_extintores WHERE numero_patrimonio = %s ORDER BY data_inspecao DESC",
        (numero_patrimonio,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Nenhuma inspeção encontrada para este patrimônio"}), 404


@app.route("/api/inspecoes/B/<int:id_brigadista>", methods=["GET"])
def listar_inspecoes_por_brigadista(id_brigadista):
    resultado = consultar_todos_sql(
        """
        SELECT i.*, b.nome_brigadista
        FROM inspecoes_extintores i
        JOIN brigadistas b ON i.id_brigadista = b.id_brigadista
        WHERE i.id_brigadista = %s
        ORDER BY i.data_inspecao DESC
        """,
        (id_brigadista,)
    )

    if resultado:
        return jsonify(resultado)

    return jsonify({"mensagem": "Nenhuma inspeção encontrada para este brigadista"}), 404


@app.route("/api/inspecoes/<int:id_inspecao>", methods=["PUT"])
def atualizar_inspecao(id_inspecao):
    dados = request.get_json() or {}

    resultado = executar_sql(
        """
        UPDATE inspecoes_extintores
        SET id_brigadista = %s,
            numero_patrimonio = %s,
            data_inspecao = %s,
            status_manometro = %s,
            status_carga = %s,
            status_agente_disparo = %s,
            lacre_rompido = %s,
            data_teste_nivel1 = %s,
            data_teste_nivel2 = %s,
            data_teste_nivel3 = %s,
            integridade_visual = %s,
            arquivo_evidencia_imagem_path = %s
        WHERE id_inspecao = %s
        """,
        (
            dados["id_brigadista"],
            dados["numero_patrimonio"],
            normalizar_datetime(dados["data_inspecao"]),
            dados["status_manometro"],
            dados["status_carga"],
            dados["status_agente_disparo"],
            1 if dados.get("lacre_rompido") else 0,
            dados["data_teste_nivel1"],
            dados["data_teste_nivel2"],
            dados["data_teste_nivel3"],
            dados["integridade_visual"],
            dados.get("arquivo_evidencia_imagem_path") or "sem_arquivo",
            id_inspecao
        )
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Inspeção não encontrada"}), 404

    return jsonify({"mensagem": "Inspeção atualizada"})


@app.route("/api/inspecoes/<int:id_inspecao>", methods=["DELETE"])
def deletar_inspecao(id_inspecao):
    resultado = executar_sql(
        "DELETE FROM inspecoes_extintores WHERE id_inspecao = %s",
        (id_inspecao,)
    )

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Inspeção não encontrada"}), 404

    return jsonify({"mensagem": "Inspeção deletada"})


# ==========================================================
# ROTAS: NOTIFICAÇÕES
# ==========================================================

@app.route("/api/notificar/verificar", methods=["POST"])
def verificar_vencimentos():
    dados = request.get_json(silent=True) or {}
    dias_alerta = int(dados.get("dias_alerta", 30))

    registros = consultar_todos_sql("""
        SELECT
            b.nome_brigadista,
            b.whatsapp,
            b.id_brigadista,
            i.numero_patrimonio,
            i.data_vencimento_nivel1
        FROM inspecoes_extintores i
        JOIN brigadistas b ON i.id_brigadista = b.id_brigadista
    """)

    notificacoes_criadas = 0
    hoje = datetime.now().date()

    for reg in registros:
        data_vencimento_texto = reg.get("data_vencimento_nivel1")
        if not data_vencimento_texto:
            continue

        data_vencimento = datetime.fromisoformat(data_vencimento_texto).date()
        dias_para_vencimento = (data_vencimento - hoje).days

        if dias_para_vencimento < 0 or dias_para_vencimento > dias_alerta:
            continue

        existente = consultar_um_sql("""
            SELECT id_notificacao
            FROM notificacoes_vencimento
            WHERE numero_patrimonio = %s
              AND id_brigadista = %s
              AND enviado = FALSE
        """, (reg["numero_patrimonio"], reg["id_brigadista"]))

        if existente:
            continue

        executar_sql("""
            INSERT INTO notificacoes_vencimento
            (numero_patrimonio, id_brigadista, dias_para_vencimento, data_verificacao, enviado)
            VALUES (%s, %s, %s, NOW(), FALSE)
        """, (reg["numero_patrimonio"], reg["id_brigadista"], dias_para_vencimento))

        notificacoes_criadas += 1

    return jsonify({
        "mensagem": f"{notificacoes_criadas} notificação(ões) criada(s)",
        "notificacoes_criadas": notificacoes_criadas,
        "dias_alerta": dias_alerta
    })


@app.route("/api/notificacoes/pendentes", methods=["GET"])
def obter_notificacoes_pendentes():
    resultado = consultar_todos_sql("""
        SELECT
            n.id_notificacao,
            n.numero_patrimonio,
            n.id_brigadista,
            n.dias_para_vencimento,
            n.data_verificacao,
            n.enviado,
            n.data_envio,
            e.tipo_agente,
            e.localizacao_detalhada,
            b.nome_brigadista,
            b.whatsapp
        FROM notificacoes_vencimento n
        JOIN extintores e ON n.numero_patrimonio = e.numero_patrimonio
        JOIN brigadistas b ON n.id_brigadista = b.id_brigadista
        WHERE n.enviado = FALSE
        ORDER BY n.dias_para_vencimento ASC
    """)

    return jsonify(resultado)


@app.route("/api/notificacoes", methods=["GET"])
def listar_notificacoes():
    resultado = consultar_todos_sql("""
        SELECT
            n.*,
            e.tipo_agente,
            e.localizacao_detalhada,
            b.nome_brigadista,
            b.whatsapp
        FROM notificacoes_vencimento n
        JOIN extintores e ON n.numero_patrimonio = e.numero_patrimonio
        JOIN brigadistas b ON n.id_brigadista = b.id_brigadista
        ORDER BY n.data_verificacao DESC
    """)

    return jsonify(resultado)


@app.route("/api/notificacoes/<int:id_notificacao>/marcar-enviada", methods=["PUT"])
def marcar_notificacao_enviada(id_notificacao):
    resultado = executar_sql("""
        UPDATE notificacoes_vencimento
        SET enviado = TRUE, data_envio = NOW()
        WHERE id_notificacao = %s
    """, (id_notificacao,))

    if resultado["rowcount"] == 0:
        return jsonify({"mensagem": "Notificação não encontrada"}), 404

    return jsonify({"mensagem": "Notificação marcada como enviada"})


@app.route("/api/notificacoes/<int:id_notificacao>/enviar", methods=["POST"])
def enviar_notificacao(id_notificacao):
    notificacao = consultar_um_sql("""
        SELECT
            n.id_notificacao,
            n.numero_patrimonio,
            n.dias_para_vencimento,
            e.tipo_agente,
            e.localizacao_detalhada,
            b.nome_brigadista,
            b.whatsapp
        FROM notificacoes_vencimento n
        JOIN extintores e ON n.numero_patrimonio = e.numero_patrimonio
        JOIN brigadistas b ON n.id_brigadista = b.id_brigadista
        WHERE n.id_notificacao = %s
    """, (id_notificacao,))

    if not notificacao:
        return jsonify({"mensagem": "Notificação não encontrada"}), 404

    mensagem = (
        f"Olá, {notificacao['nome_brigadista']}! "
        f"O extintor {notificacao['numero_patrimonio']} ({notificacao['tipo_agente']}) "
        f"localizado em {notificacao['localizacao_detalhada']} vence em "
        f"{notificacao['dias_para_vencimento']} dia(s). "
        f"Por favor, providencie a verificação."
    )

    resultado_envio = enviar_whatsapp(notificacao["whatsapp"], mensagem)

    if resultado_envio["enviado"]:
        executar_sql("""
            UPDATE notificacoes_vencimento
            SET enviado = TRUE, data_envio = NOW()
            WHERE id_notificacao = %s
        """, (id_notificacao,))

    status = 200 if resultado_envio["enviado"] else 400

    return jsonify(resultado_envio), status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
