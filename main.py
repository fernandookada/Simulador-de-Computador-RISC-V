"""
Programa de Teste Final (Semana 6) - Simulador RISC-V (Grupo 11)

Demonstra o funcionamento completo do simulador integrando:
  1. CPU RV32I completa (Tipos R, I, S, B, U, J) + Instrução exclusiva CTZ (Grupo 11)
  2. Memória RAM (0x00000 - 0x7FFFF) e VRAM (0x80000 - 0x8FFFF)
  3. Barramento (dados, endereços e controle)
  4. E/S Programada: escrita de caracteres ASCII na VRAM via `SW` e transmissão
     periódica ao terminal a cada `n` instruções executadas.

Algoritmo equivalente em C (traduzido para RV32I + CTZ):
--------------------------------------------------------
int calcular_ctz_soma(int a, int b) {
    // a = 80 (0b1010000 -> ctz = 4), b = 8 (0b1000 -> ctz = 3)
    int z1 = __builtin_ctz(a);
    int z2 = __builtin_ctz(b);
    return z1 + z2; // retorna 7
}

void main() {
    int a = 20 << 2; // 80
    int b = 13 - 5;  // 8
    int soma = 0;
    // Laço (Branch) que acumula o resultado
    for (int i = 0; i < 1; i++) {
        soma = calcular_ctz_soma(a, b);
    }
    MEM[0x400] = soma;
    int lido = MEM[0x400];

    // Escreve "G11:CTZ=7" na VRAM (0x80000) usando Store Word (SW)
    VRAM[0] = 'G'; VRAM[1] = '1'; VRAM[2] = '1'; VRAM[3] = ':';
    VRAM[4] = 'C'; VRAM[5] = 'T'; VRAM[6] = 'Z'; VRAM[7] = '=';
    VRAM[8] = '0' + lido; // '7' (ASCII 55)
}
"""
from simulador import Simulador


# Pequenos auxiliares para montar as instruções de 32 bits do programa de teste
def tipo_r(funct7, rs2, rs1, funct3, rd, opcode=0b0110011):
    return (funct7 << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def tipo_i(imm, rs1, funct3, rd, opcode=0b0010011):
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (funct3 << 12) | (rd << 7) | opcode


def tipo_s(imm, rs2, rs1, funct3=0b010, opcode=0b0100011):
    imm &= 0xFFF
    return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (funct3 << 12) | ((imm & 0x1F) << 7) | opcode


def tipo_b(imm, rs2, rs1, funct3, opcode=0b1100011):
    imm &= 0x1FFF
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) \
        | (funct3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | opcode


def tipo_u(imm20, rd, opcode=0b0110111):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode


def tipo_j(imm, rd, opcode=0b1101111):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) \
        | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | opcode


def addi(rd, rs1, imm):
    return tipo_i(imm, rs1, 0b000, rd)


def sw(rs2, rs1, imm):
    return tipo_s(imm, rs2, rs1)


def lw(rd, rs1, imm):
    return tipo_i(imm, rs1, 0b010, rd, 0b0000011)


def ctz(rd, rs1):
    # Instrução exclusiva do Grupo 11 (Zbb): funct7=0110000, shamt=00001, funct3=001
    return tipo_i((0b0110000 << 5) | 0b00001, rs1, 0b001, rd)


programa_teste = [
    # --- 1. Preparação dos operandos (Tipo-I e Tipo-R) ------------------------
    addi(1, 0, 20),                        # 0x00: ADDI x1, x0, 20      (x1 = 20)
    tipo_i(2, 1, 0b001, 2),                # 0x04: SLLI x2, x1, 2       (x2 = 20 << 2 = 80)
    addi(3, 0, 13),                        # 0x08: ADDI x3, x0, 13      (x3 = 13)
    addi(4, 0, 5),                         # 0x0C: ADDI x4, x0, 5       (x4 = 5)
    tipo_r(0b0100000, 4, 3, 0b000, 5),     # 0x10: SUB  x5, x3, x4      (x5 = 13 - 5 = 8)

    # --- 2. Chamada de sub-rotina com JAL (Tipo-J) ----------------------------
    # Salta para a função `calcular_ctz_soma` no endereço 0x6C (+88 bytes)
    tipo_j(88, 1),                         # 0x14: JAL  x1, +88         (ra/x1 = 0x18, PC = 0x6C)

    # --- 3. Armazenamento e leitura na RAM (SW e LW) --------------------------
    sw(8, 0, 0x400),                       # 0x18: SW   x8, 0x400(x0)   (MEM[0x400] = x8 = 7)
    lw(9, 0, 0x400),                       # 0x1C: LW   x9, 0x400(x0)   (x9 = MEM[0x400] = 7)

    # --- 4. E/S Programada: Escrita de "G11:CTZ=7" na VRAM (0x80000) via SW ---
    tipo_u(0x80, 10),                      # 0x20: LUI  x10, 0x80       (x10 = 0x80000 -> base da VRAM)
    addi(11, 0, ord("G")),                 # 0x24: ADDI x11, x0, 'G'    (71)
    sw(11, 10, 0),                         # 0x28: SW   x11, 0(x10)     (VRAM[0x80000] = 'G')
    addi(11, 0, ord("1")),                 # 0x2C: ADDI x11, x0, '1'    (49)
    sw(11, 10, 4),                         # 0x30: SW   x11, 4(x10)     (VRAM[0x80004] = '1')
    sw(11, 10, 8),                         # 0x34: SW   x11, 8(x10)     (VRAM[0x80008] = '1')
    addi(11, 0, ord(":")),                 # 0x38: ADDI x11, x0, ':'    (58)
    sw(11, 10, 12),                        # 0x3C: SW   x11, 12(x10)    (VRAM[0x8000C] = ':')
    addi(11, 0, ord("C")),                 # 0x40: ADDI x11, x0, 'C'    (67)
    sw(11, 10, 16),                        # 0x44: SW   x11, 16(x10)    (VRAM[0x80010] = 'C')
    addi(11, 0, ord("T")),                 # 0x48: ADDI x11, x0, 'T'    (84)
    sw(11, 10, 20),                        # 0x4C: SW   x11, 20(x10)    (VRAM[0x80014] = 'T')
    addi(11, 0, ord("Z")),                 # 0x50: ADDI x11, x0, 'Z'    (90)
    sw(11, 10, 24),                        # 0x54: SW   x11, 24(x10)    (VRAM[0x80018] = 'Z')
    addi(11, 0, ord("=")),                 # 0x58: ADDI x11, x0, '='    (61)
    sw(11, 10, 28),                        # 0x5C: SW   x11, 28(x10)    (VRAM[0x8001C] = '=')
    addi(11, 9, ord("0")),                 # 0x60: ADDI x11, x9, '0'    (converte 7 para ASCII '7' = 55)
    sw(11, 10, 32),                        # 0x64: SW   x11, 32(x10)    (VRAM[0x80020] = '7')

    # --- 5. Desvio Condicional (Branch - Tipo-B) para encerrar o programa -----
    # BEQ x8, x9, +20 -> Como x8 (7) == x9 (7), salta sobre a sub-rotina para 0x7C (HALT)
    tipo_b(20, 9, 8, 0b000),               # 0x68: BEQ  x8, x9, +20     (PC = 0x68 + 20 = 0x7C -> HALT)

    # --- Sub-rotina `calcular_ctz_soma` (endereço 0x6C) -----------------------
    ctz(6, 2),                             # 0x6C: CTZ  x6, x2          ([GRUPO 11] ctz(80) = 4)
    ctz(7, 5),                             # 0x70: CTZ  x7, x5          ([GRUPO 11] ctz(8)  = 3)
    tipo_r(0b0000000, 7, 6, 0b000, 8),     # 0x74: ADD  x8, x6, x7      (x8 = 4 + 3 = 7)
    tipo_i(0, 1, 0b000, 0, 0b1100111),     # 0x78: JALR x0, 0(x1)       (retorna para 0x18)
]


def main():
    # Define n = 5: a cada 5 instruções executadas, a VRAM é transmitida ao terminal
    n_instrucoes = 5
    simulador = Simulador(intervalo_vram=n_instrucoes)

    print("=" * 72)
    print(" SIMULADOR DE COMPUTADOR RISC-V (RV32I) - GRUPO 11 (Instrução: CTZ)")
    print(f" E/S Programada: Transmissão da VRAM ao terminal a cada n = {n_instrucoes} instruções")
    print("=" * 72 + "\n")

    simulador.carregar(programa_teste, endereco_inicial=0x0)
    executadas = simulador.executar(verbose=True)

    print("\n--- Conteúdo Final da VRAM (0x80000) ---")
    print(f"Texto ASCII na VRAM: {simulador.memoria.ler_vram_ascii()}")

    simulador.cpu.mostrar_resumo()

    print("\n--- Estatísticas do Simulador ---")
    print(f"Instruções executadas     : {executadas}")
    print(f"Leituras no barramento    : {simulador.barramento.leituras}")
    print(f"Escritas no barramento    : {simulador.barramento.escritas}")
    print(f"Transmissões VRAM (a cada {n_instrucoes}): {len(simulador.transmissoes_vram)}")


if __name__ == "__main__":
    main()
