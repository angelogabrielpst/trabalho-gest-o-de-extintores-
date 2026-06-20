-- CASO OCORRA ERROS
drop database sst_extintores_db;


-- CRIAR O BANCO DE DADOS
create database sst_extintores_db;
USE sst_extintores_db;


-- TABELA DIMENSÃO
create table setores_loc (
	id_setor int auto_increment primary key,
    nome_setor varchar(100) not null,
    bloco_pavimento varchar(50) not null
    ) ENGINE=InnoDB;



    -- TABELA DIMENSÃO
create table brigadistas (
	id_brigadista int auto_increment primary key,
    nome_brigadista varchar(50),
    cpf varchar(20) unique not null,
    telefone varchar(20) not null,
    email varchar(320),
    whatsapp varchar(20),
    data_treinamento date,
    id_setor int not null,
    foreign key (id_setor) references setores_loc(id_setor) on delete restrict
    ) ENGINE=InnoDB;
    
    
-- TABELA DIMENSÃO
create table extintores (
	numero_patrimonio varchar(50) primary key,
    id_setor int not null,
    codigo_lacre varchar(30) unique not null,
    tipo_agente enum ("Água", "PQS", "CO2", "Espuma") not null,
    classe_incendio enum ("A", "B", "AB", "ABC", "BC"),
    localizacao_detalhada varchar(150) not null,
    validade_carga date not null,
	data_aquisicao date not null,
    data_ultima_recarga date not null,
    extintor_status enum ("Disponível", "Vencido", "Em manutenção", "Reserva", "Condenado"),
    foreign key (id_setor) references setores_loc(id_setor) on delete restrict
    ) ENGINE=InnoDB;
    
    
    -- TABELA FATO
create table inspecoes_extintores (
	id_inspecao int auto_increment primary key,
    id_brigadista int not null,
    numero_patrimonio varchar(50),
    data_inspecao datetime not null,
    status_manometro enum ("Pressão Padrão", "Baixa Pressão", "Alta Pressão") not null,
    status_carga enum ("Cheio", "Vazio", "Parcial") not null,
    status_agente_disparo enum ("Conforme", "Inconforme") not null,
    lacre_rompido tinyint default 0,
    data_teste_nivel1 date not null,
    data_teste_nivel2 date not null,
    data_teste_nivel3 date not null,
    data_vencimento_nivel1 date not null,
    data_vencimento_nivel2 date not null,
    data_vencimento_nivel3 date not null,
    integridade_visual enum ("Excelente", "Avariado/Amassado", "Corroído") not null,
    arquivo_evidencia_imagem_path varchar(255) not null,
    foreign key (numero_patrimonio) references extintores(numero_patrimonio) on delete restrict,
    foreign key (id_brigadista) references brigadistas(id_brigadista) on delete restrict
    ) ENGINE=InnoDB;
    
    
    
-- Calculando vencimentos na tabela inspecoes_extintores
    update inspeçoes_extintores
    set 
		-- Nível 1 (Inspeção Visual) Deve ser realizada mensalmente: Validade de 1 mês 
        data_vencimento_nivel1 = date_add(data_teste_nivel1, interval 1 month),
        
        -- Nível 2 (Recarrga/Preventiva) Ocorre a cada 12 meses: Validade de 1 ano (12 meses)
        data_vencimento_nivel2 = date_add(data_teste_nivel2, interval 1 year),
        
        -- Nível 3 (Teste Hidrostático): Validade de 5 anos
        data_vencimento_nivel3 = date_add(data_teste_nivel3, interval 5 year);
        
-- Teste de Cálculo Direto (Sem Inserir Dados)
	SELECT
		'2024-06-17' as data_teste,
        DATE_ADD('2024-06-17', INTERVAL 1 MONTH) AS vencimento_nivel1, -- Esperado: 2024-07-17
		DATE_ADD('2024-06-17', INTERVAL 1 YEAR) AS vencimento_nivel2,  -- Esperado: 2025-06-17
		DATE_ADD('2024-06-17', INTERVAL 5 YEAR) AS vencimento_nivel3;  -- Esperado: 2029-06-17

	

    
    


    
    
    