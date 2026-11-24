"""
Simulador: monta o computador (Memória + Barramento + CPU) e roda o ciclo da CPU.

Ciclo da CPU (PDF do projeto):
    1. O PC aponta para um endereço da memória principal.
    2. A instrução é enviada da memória para o processador (pelo barramento).
    3. O processador decodifica a instrução.
    4. O processador executa (ULA), armazena o resultado e atualiza o PC.
    5. A cada `n` instruções executadas (E/S Programada), transmite o conteúdo
       ASCII da memória VRAM para o terminal.
"""
from memoria import Memoria
from barramento import Barramento
from cpu import CPU


class Simulador:
    INSTRUCAO_HALT = 0x00000000  # memória vazia: encerra a execução

    def __init__(self, intervalo_vram: int | None = None):
        self.memoria = Memoria()
        self.barramento = Barramento(self.memoria)
        self.cpu = CPU(self.barramento)
        # Quantidade n de instruções entre cada transmissão da VRAM ao terminal
        self.intervalo_vram = intervalo_vram
        # Histórico de transmissões da VRAM: lista de tuplas (ciclo, texto_ascii)
        self.transmissoes_vram: list[tuple[int, str]] = []

    def carregar(self, programa, endereco_inicial: int = 0):
        """Grava o programa na memória e aponta o PC para a primeira instrução."""
        self.memoria.carregar_programa(programa, endereco_inicial)
        self.cpu.pc = endereco_inicial

    def transmitir_vram(self, ciclo: int, imprimir: bool = True) -> str:
        """Lê os caracteres ASCII da VRAM e transmite via terminal."""
        texto = self.memoria.ler_vram_ascii()
        self.transmissoes_vram.append((ciclo, texto))
        if imprimir:
            exibicao = texto if texto else "(vazia)"
            print(f"[VRAM | Ciclo {ciclo:02d}] Terminal: {exibicao}")
        return texto

    def executar(
        self,
        max_ciclos: int = 10_000,
        verbose: bool = False,
        intervalo_vram: int | None = None,
        imprimir_vram: bool = True,
    ) -> int:
        """
        Loop de busca, decodificação e execução.
        Para ao buscar a instrução 0x00000000 (halt) ou ao atingir max_ciclos.
        Se `intervalo_vram` (n) for definido (> 0), exibe no terminal os caracteres
        ASCII presentes na VRAM a cada `n` instruções executadas.
        Devolve o número de instruções executadas.
        """
        n = intervalo_vram if intervalo_vram is not None else self.intervalo_vram
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

            # E/S Programada (Semana 6): transmite a VRAM ao terminal a cada n instruções
            if n is not None and n > 0 and (executadas % n == 0):
                self.transmitir_vram(executadas, imprimir=imprimir_vram)

        return executadas
