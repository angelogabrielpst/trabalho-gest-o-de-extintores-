from dataclasses import dataclass

@dataclass
class extintor:
       n_cilindro = int
       n_lacre = int
       cor_lacre = str
       classificacao = str
       agente = str
       capacidade = int
       validade = int #transformar em data depois
       
       

def inf_extintor(self):
        print(f"""
    Número do Cilindro: {self.n_cilindro}
    Número do Lacre: {self.lacre}
    Cor do lacre: {self.cor_lacre}
    Classificação: {self.classificacao}
    Agente: {self.agente}
    """)
       

@dataclass
class extintor_co2(extintor):
    tipo: str = 'CO²'
    pressao: int


@dataclass
class extintor_recarregavel(extintor):
    tipo: str = 'Recarregável'
    data_ult_inspecao:
    nivel_manut_executado:
'''


'''Print (
       Número do Cilindro: 
       Número do Lacre:
       Cor do lacre:
       Classificação:
       Agente:
)'''