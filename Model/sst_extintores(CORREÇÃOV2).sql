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
    
    
-- TABELA FATO
create table extintores (
	numero_patrimonio varchar(50) primary key,
    id_setor int not null,
    codigo_lacre varchar(30) unique not null,
    tipo_agente enum ("Agua", "PQS", "CO2", "Espuma") not null,
    classe_incendio enum ("A", "B", "AB", "ABC"),
    localizacao_detalhada varchar(150) not null,
    id_brigadista_responsavel int not null,
    validade_carga date not null,
    foreign key (id_setor) references setores_loc(id_setor) on delete restrict
    ) ENGINE=InnoDB;
    
create table inspecoes_extintores (
	id_inspecao int auto_increment primary key,
    numero_patrimonio varchar(50),
    data_inspecao datetime not null,
    status_manometro enum ("Conforme", "Inconforme") not null,
    status_agente_disparo enum ("Conforme", "Inconforme") not null,
    lacre_rompido tinyint default 0,
    validade_teste_nivel1 date not null,
    validade_teste_nivel2 date not null,
    validade_teste_nivel3 date not null,
    integridade_visual enum ("Excelente", "Avariado/Amassado", "Corroído") not null,
    arquivo_evidencia_imagem_path varchar(255) not null,
    foreign key (numero_patrimonio) references extintores(numero_patrimonio) on delete restrict
    ) ENGINE=InnoDB;
    
    