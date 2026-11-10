from cpu import CPU

cpu = CPU()

# Lista de instruções em binário separadas por underline conforme os formatos da Figura 3 do PDF
programa_teste = [
    # 1. Tipo-I (Imediato): imm[11:0] _ rs1 _ funct3 _ rd _ opcode (0010011)
    (0b000000010100_00000_000_00001_0010011, "ADDI x1, x0, 20   (x1 = 0 + 20 = 20)"),
    (0b000000000101_00000_000_00010_0010011, "ADDI x2, x0, 5    (x2 = 0 + 5 = 5)"),
    (0b0000000_00010_00001_001_00011_0010011, "SLLI x3, x1, 2    (x3 = 20 << 2 = 80)"),

    # 2. Tipo-R (Registradores): funct7 _ rs2 _ rs1 _ funct3 _ rd _ opcode (0110011)
    (0b0000000_00010_00001_000_00100_0110011, "ADD  x4, x1, x2   (x4 = 20 + 5 = 25)"),
    (0b0100000_00010_00001_000_00101_0110011, "SUB  x5, x1, x2   (x5 = 20 - 5 = 15)"),

    # Instrução Especial Exclusiva do Grupo 11: CTZ (Count Trailing Zeros - Extensão Zbb)
    # Conta quantos bits 0 existem à direita em x3 (80 em binário é 1010000 -> 4 zeros à direita)
    # Formato: funct7(0110000) _ shamt(00001) _ rs1(x3) _ funct3(001) _ rd(x7) _ opcode(0010011)
    (0b0110000_00001_00011_001_00111_0010011, "CTZ  x7, x3       ([GRUPO 11] zeros à direita de 80 (1010000b) -> x7 = 4)"),

    # 3. Acesso à Memória (SW e LW):
    # SW x4, 8(x0) -> Salva o valor de x4 (25) no endereço de memória 0 + 8 = 8
    # Formato Tipo-S: imm[11:5] _ rs2 _ rs1 _ funct3(010) _ imm[4:0] _ opcode(0100011)
    (0b0000000_00100_00000_010_01000_0100011, "SW   x4, 8(x0)    (MEM[8] = x4 = 25)"),

    # LW x6, 8(x0) -> Lê o valor do endereço 8 da memória e guarda em x6
    # Formato Tipo-I: imm[11:0] _ rs1 _ funct3(010) _ rd _ opcode(0000011)
    (0b000000001000_00000_010_00110_0000011, "LW   x6, 8(x0)    (x6 = MEM[8] = 25)"),

    # 4. Desvio Condicional (Branch - Tipo-B):
    # BEQ x4, x6, 12 -> Como x4 (25) == x6 (25), o PC avança +12 em vez de +4!
    # Formato Tipo-B: imm[12|10:5] _ rs2 _ rs1 _ funct3(000) _ imm[4:1|11] _ opcode(1100011)
    (0b0_000000_00110_00100_000_0110_0_1100011, "BEQ  x4, x6, 12   (x4 == x6 -> salta PC em +12)"),
]

print("Iniciando simulação da CPU (Tipos R, I, Acesso à Memória e Branch):\n")

for instrucao, descricao in programa_teste:
    pc_antes = cpu.pc
    campos = cpu.executar_ciclo(instrucao)
    print(f"[PC {pc_antes:02d} -> {cpu.pc:02d}] {descricao}")

cpu.mostrar_resumo()
