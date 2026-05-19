from dataclasses import dataclass, KW_ONLY
from datetime import date
#Classe para os setores
@dataclass
class Setor:
    id_setor: int
    nome_setor: str
    bloco_pavimento: str

    def inf_Setor(self):
        print(f'''
        ID do Setor: {self.id_setor}
        Setor: {self.nome_setor}
        Bloco: {self.bloco_pavimento}
              ''')
        
#Classe que engloba todos os extintores
@dataclass
class Extintor:
    recarregavel: bool
    numero_patrimonio: int
    codigo_lacre: int
    cor_lacre: str
    classe_incendio: str
    tipo_agente: str
    capacidade: int
    validade_carga: date 
    
    #Função pra mostrar o extintor
    def inf_extintor(self):
        print(f"""
    Extintor Recarregável: {self.recarregavel}
    Número do Cilindro: {self.numero_patrimonio}
    Número do Lacre: {self.codigo_lacre}
    Cor do lacre: {self.cor_lacre}
    Classificação: {self.classe_incendio}
    Agente: {self.tipo_agente}
    Capacidade: {self.capacidade}Kg
    Validade: {self.validade.strftime}
    """)
       
       #pensando em tirar
'''
@dataclass
class ExtintorRecarregavel(Extintor):
    _: KW_ONLY
    tipo: str = 'Recarregável'
    data_ult_inspecao: date = None
    nivel_manut_executado: str = 'Nenhum'
'''

#inspeções
@dataclass
class Inspecoes:
    id_inspecao: int
    numero_patrimonio: str