-- CASO OCORRA ERROS
DROP DATABASE IF EXISTS sst_extintores_db;


-- CRIAR O BANCO DE DADOS
CREATE DATABASE sst_extintores_db;
USE sst_extintores_db;


-- TABELA DIMENSÃO
CREATE TABLE setores_loc (
    id_setor INT AUTO_INCREMENT PRIMARY KEY,
    nome_setor VARCHAR(100) NOT NULL,
    bloco_pavimento VARCHAR(50) NOT NULL
) ENGINE=InnoDB;


-- TABELA DIMENSÃO
CREATE TABLE brigadistas (
    id_brigadista INT AUTO_INCREMENT PRIMARY KEY,
    nome_brigadista VARCHAR(50),
    cpf VARCHAR(20) UNIQUE NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(320),
    whatsapp VARCHAR(20),
    data_treinamento DATE,
    id_setor INT NOT NULL,
    FOREIGN KEY (id_setor) REFERENCES setores_loc(id_setor) ON DELETE RESTRICT
) ENGINE=InnoDB;
    
    
-- TABELA DIMENSÃO
CREATE TABLE extintores (
    numero_patrimonio VARCHAR(50) PRIMARY KEY,
    id_setor INT NOT NULL,
    codigo_lacre VARCHAR(30) UNIQUE NOT NULL,
    tipo_agente ENUM ("Água", "PQS", "CO2", "Espuma") NOT NULL,
    classe_incendio ENUM ("A", "B", "AB", "ABC", "BC"),
    localizacao_detalhada VARCHAR(150) NOT NULL,
    validade_carga DATE NOT NULL,
    data_aquisicao DATE NOT NULL,
    data_ultima_recarga DATE NOT NULL,
    extintor_status ENUM ("Disponível", "Vencido", "Em manutenção", "Reserva", "Condenado"),
    FOREIGN KEY (id_setor) REFERENCES setores_loc(id_setor) ON DELETE RESTRICT
) ENGINE=InnoDB;
    
    
-- TABELA FATO
CREATE TABLE inspecoes_extintores (
    id_inspecao INT AUTO_INCREMENT PRIMARY KEY,
    id_brigadista INT NOT NULL,
    numero_patrimonio VARCHAR(50),
    data_inspecao DATETIME NOT NULL,
    status_manometro ENUM ("Pressão Padrão", "Baixa Pressão", "Alta Pressão") NOT NULL,
    status_carga ENUM ("Cheio", "Vazio", "Parcial") NOT NULL,
    status_agente_disparo ENUM ("Conforme", "Inconforme") NOT NULL,
    lacre_rompido TINYINT DEFAULT 0,
    data_teste_nivel1 DATE NOT NULL,
    data_teste_nivel2 DATE NOT NULL,
    data_teste_nivel3 DATE NOT NULL,
    data_vencimento_nivel1 DATE NOT NULL,
    data_vencimento_nivel2 DATE NOT NULL,
    data_vencimento_nivel3 DATE NOT NULL,
    integridade_visual ENUM ("Excelente", "Avariado/Amassado", "Corroído") NOT NULL,
    arquivo_evidencia_imagem_path VARCHAR(255) NOT NULL,
    FOREIGN KEY (numero_patrimonio) REFERENCES extintores(numero_patrimonio) ON DELETE RESTRICT,
    FOREIGN KEY (id_brigadista) REFERENCES brigadistas(id_brigadista) ON DELETE RESTRICT
) ENGINE=InnoDB;
    
    
-- Desativa temporariamente a trava de segurança para permitir o update em massa
SET SQL_SAFE_UPDATES = 0;

-- Calculando vencimentos na tabela inspecoes_extintores (CORRIGIDO: 'inspecoes' sem ç)
UPDATE inspecoes_extintores
SET 
    -- Nível 1 (Inspeção Visual) Deve ser realizada mensalmente: Validade de 1 mês 
    data_vencimento_nivel1 = DATE_ADD(data_teste_nivel1, INTERVAL 1 MONTH),
    
    -- Nível 2 (Recarga/Preventiva) Ocorre a cada 12 meses: Validade de 1 ano (12 meses)
    data_vencimento_nivel2 = DATE_ADD(data_teste_nivel2, INTERVAL 1 YEAR),
    
    -- Nível 3 (Teste Hidrostático): Validade de 5 anos
    data_vencimento_nivel3 = DATE_ADD(data_teste_nivel3, INTERVAL 5 YEAR);

-- Reativa a trava de segurança do Workbench
SET SQL_SAFE_UPDATES = 1;
        
-- Teste de Cálculo Direto (Sem Inserir Dados)
SELECT
    '2024-06-17' AS data_teste,
    DATE_ADD('2024-06-17', INTERVAL 1 MONTH) AS vencimento_nivel1, -- Esperado: 2024-07-17
    DATE_ADD('2024-06-17', INTERVAL 1 YEAR) AS vencimento_nivel2,  -- Esperado: 2025-06-17
    DATE_ADD('2024-06-17', INTERVAL 5 YEAR) AS vencimento_nivel3;  -- Esperado: 2029-06-17
