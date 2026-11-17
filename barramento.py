"""
Barramento do simulador: liga a CPU à Memória.

Conforme o PDF do projeto, o barramento é dividido em 3 partes:
    1. Barramento de dados     (32 bits): o valor que trafega entre os blocos.
    2. Barramento de endereços (32 bits): a posição de memória a ser lida/escrita.
    3. Barramento de controle:            a permissão de leitura ou escrita.

Toda comunicação da CPU com a memória (busca de instruções, LW e SW) passa por
aqui. Cada transação preenche as três linhas e, ao terminar, o sinal de controle
volta para NENHUM (barramento ocioso). Os valores de dados e endereços ficam
visíveis até a próxima transação, o que permite inspecionar o último acesso.
"""
from memoria import Memoria


class Barramento:
    # Sinais possíveis do barramento de controle
    NENHUM = 0   # barramento ocioso
    LEITURA = 1  # a memória coloca o valor no barramento de dados
    ESCRITA = 2  # a memória grava o valor que está no barramento de dados

    def __init__(self, memoria: Memoria):
        self.memoria = memoria

        # As 3 partes do barramento
        self.dados = 0                 # barramento de dados (32 bits)
        self.enderecos = 0             # barramento de endereços (32 bits)
        self.controle = self.NENHUM    # barramento de controle (leitura/escrita)

        # Métricas para o relatório final
        self.leituras = 0
        self.escritas = 0

    def ler(self, endereco: int) -> int:
        """
        Transação de leitura: a CPU coloca o endereço, sinaliza LEITURA e a
        memória devolve a palavra de 32 bits pelo barramento de dados.
        Erros de memória (ErroMemoria) são propagados para quem chamou.
        """
        self.enderecos = endereco & 0xFFFFFFFF
        self.controle = self.LEITURA
        try:
            valor = self.memoria.ler_palavra(self.enderecos)
            self.dados = valor & 0xFFFFFFFF
            self.leituras += 1
            return self.dados
        finally:
            self.controle = self.NENHUM

    def escrever(self, endereco: int, valor: int):
        """
        Transação de escrita: a CPU coloca o endereço e o valor, sinaliza
        ESCRITA e a memória grava a palavra que está no barramento de dados.
        Erros de memória (ErroMemoria) são propagados para quem chamou.
        """
        self.enderecos = endereco & 0xFFFFFFFF
        self.dados = valor & 0xFFFFFFFF
        self.controle = self.ESCRITA
        try:
            self.memoria.escrever_palavra(self.enderecos, self.dados)
            self.escritas += 1
        finally:
            self.controle = self.NENHUM
