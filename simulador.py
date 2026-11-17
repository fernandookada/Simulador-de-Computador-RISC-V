"""
Simulador: monta o computador (Memória + Barramento + CPU) e roda o ciclo da CPU.

Ciclo da CPU (PDF do projeto):
    1. O PC aponta para um endereço da memória principal.
    2. A instrução é enviada da memória para o processador (pelo barramento).
    3. O processador decodifica a instrução.
    4. O processador executa (ULA), armazena o resultado e atualiza o PC.
"""
from memoria import Memoria
from barramento import Barramento
from cpu import CPU


class Simulador:
    INSTRUCAO_HALT = 0x00000000  # memória vazia: encerra a execução

    def __init__(self):
        self.memoria = Memoria()
        self.barramento = Barramento(self.memoria)
        self.cpu = CPU(self.barramento)

    def carregar(self, programa, endereco_inicial: int = 0):
        """Grava o programa na memória e aponta o PC para a primeira instrução."""
        self.memoria.carregar_programa(programa, endereco_inicial)
        self.cpu.pc = endereco_inicial

    def executar(self, max_ciclos: int = 10_000, verbose: bool = False) -> int:
        """
        Loop de busca, decodificação e execução.
        Para ao buscar a instrução 0x00000000 (halt) ou ao atingir max_ciclos.
        Devolve o número de instruções executadas.
        """
        executadas = 0
        while executadas < max_ciclos:
            pc = self.cpu.pc
            instrucao = self.cpu.buscar()          # 1 e 2: busca pelo PC via barramento
            if instrucao == self.INSTRUCAO_HALT:   # halt verificado antes de executar
                break
            if verbose:
                print(f"[PC 0x{pc:05X}] 0x{instrucao:08X}")
            self.cpu.executar_ciclo(instrucao)     # 3 e 4: decodifica, executa, atualiza PC
            executadas += 1

            # TODO semana 6: imprimir a VRAM no terminal a cada n ciclos

        return executadas
