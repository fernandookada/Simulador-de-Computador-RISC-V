"""
Memória principal do simulador (RAM + VRAM + Periféricos).

Mapeamento de endereços (PDF do projeto):
    0x00000 - 0x7FFFF  RAM Principal (Programa, Dados, Pilha, Heap)
    0x80000 - 0x8FFFF  VRAM (Vídeo RAM)
    0x90000 - 0x9FBFF  Área Reservada para Expansão Futura  -> acesso bloqueado
    0x9FC00 - 0x9FFFF  Periféricos de Hardware (E/S Mapeada)

A memória é endereçada por byte, como no RISC-V: cada endereço guarda 8 bits,
e uma palavra (word) de 32 bits ocupa 4 endereços consecutivos, armazenados em
little-endian (byte menos significativo no menor endereço).
"""


class ErroMemoria(Exception):
    """Acesso inválido: endereço fora do mapa, área reservada ou desalinhado."""


class Memoria:
    # (início, fim, nome, permite_acesso)
    REGIOES = [
        (0x00000, 0x7FFFF, "RAM", True),
        (0x80000, 0x8FFFF, "VRAM", True),
        (0x90000, 0x9FBFF, "RESERVADA", False),
        (0x9FC00, 0x9FFFF, "PERIFERICOS", True),
    ]

    INICIO_RAM = 0x00000
    INICIO_VRAM = 0x80000
    FIM_VRAM = 0x8FFFF
    INICIO_PERIFERICOS = 0x9FC00
    TAMANHO = 0xA0000  # 640 KiB: do endereço 0x00000 até 0x9FFFF

    def __init__(self):
        self.dados = bytearray(self.TAMANHO)  # todos os bytes começam em 0

    # -------------------------------------------------------------------------
    # Validação de endereços
    # -------------------------------------------------------------------------
    def regiao(self, endereco: int) -> str:
        """Retorna o nome da região a que o endereço pertence."""
        for inicio, fim, nome, _ in self.REGIOES:
            if inicio <= endereco <= fim:
                return nome
        raise ErroMemoria(f"Endereço 0x{endereco:05X} fora do mapa de memória")

    def _validar(self, endereco: int, tamanho: int):
        """Garante que todos os bytes do acesso estão numa região permitida."""
        if endereco % tamanho != 0:
            raise ErroMemoria(
                f"Endereço 0x{endereco:05X} desalinhado para acesso de {tamanho} bytes"
            )
        for inicio, fim, nome, permite in self.REGIOES:
            if inicio <= endereco <= fim:
                if not permite:
                    raise ErroMemoria(f"Acesso bloqueado à área {nome} (0x{endereco:05X})")
                if endereco + tamanho - 1 > fim:
                    raise ErroMemoria(f"Acesso em 0x{endereco:05X} ultrapassa o fim da região {nome}")
                return
        raise ErroMemoria(f"Endereço 0x{endereco:05X} fora do mapa de memória")

    # -------------------------------------------------------------------------
    # Leitura e escrita
    # -------------------------------------------------------------------------
    def ler_byte(self, endereco: int) -> int:
        self._validar(endereco, 1)
        return self.dados[endereco]

    def escrever_byte(self, endereco: int, valor: int):
        self._validar(endereco, 1)
        self.dados[endereco] = valor & 0xFF

    def ler_palavra(self, endereco: int) -> int:
        """Lê 32 bits (4 bytes, little-endian). Usado por LW e pela busca de instruções."""
        self._validar(endereco, 4)
        return int.from_bytes(self.dados[endereco:endereco + 4], "little")

    def escrever_palavra(self, endereco: int, valor: int):
        """Escreve 32 bits (4 bytes, little-endian). Usado por SW."""
        self._validar(endereco, 4)
        self.dados[endereco:endereco + 4] = (valor & 0xFFFFFFFF).to_bytes(4, "little")

    # -------------------------------------------------------------------------
    # Utilitários
    # -------------------------------------------------------------------------
    def carregar_programa(self, instrucoes, endereco_inicial: int = INICIO_RAM):
        """Grava uma lista de instruções (palavras de 32 bits) a partir do endereço dado."""
        for i, instrucao in enumerate(instrucoes):
            self.escrever_palavra(endereco_inicial + 4 * i, instrucao)

    def ler_vram(self) -> bytes:
        """Retorna o conteúdo bruto da VRAM (usado pela saída no terminal na semana 6)."""
        return bytes(self.dados[self.INICIO_VRAM:self.FIM_VRAM + 1])

    def dump(self, inicio: int, quantidade_palavras: int = 8):
        """Mostra um trecho da memória, uma palavra por linha."""
        for i in range(quantidade_palavras):
            endereco = inicio + 4 * i
            valor = self.ler_palavra(endereco)
            print(f"[{self.regiao(endereco):<11}] 0x{endereco:05X}: 0x{valor:08X}")
