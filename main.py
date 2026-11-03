from cpu import CPU

# Instancia a CPU do Grupo 11
cpu = CPU()

# Valores iniciais para testar as operações nos registradores x1 e x2
cpu.definir_registrador(1, 20)
cpu.definir_registrador(2, 5)
cpu.definir_registrador(0, 99)  # Teste: tentar mudar o x0 (deve continuar 0)

# Lista de instruções em binário/hexadecimal de 32 bits (Tipo-R)
programa_teste = [
    (0b0000000_00010_00001_000_00011_0110011, "ADD x3, x1, x2"),  # x3 = 20 + 5 = 25
    (0b0100000_00010_00001_000_00100_0110011, "SUB x4, x1, x2"),  # x4 = 20 - 5 = 15
    (0b0000000_00010_00001_111_00101_0110011, "AND x5, x1, x2"),  # x5 = 20 & 5 = 4
    (0b0000000_00010_00001_110_00110_0110011, "OR  x6, x1, x2"),  # x6 = 20 | 5 = 21
]

print("Iniciando simulação da Semana 2 (Decodificador + Tipo-R básico):\n")

for instrucao, nome in programa_teste:
    campos = cpu.executar_ciclo(instrucao)
    print(f"Instrução: {nome}")
    print(f" -> Campos extraídos: opcode={bin(campos['opcode'])}, rd=x{campos['rd']}, rs1=x{campos['rs1']}, rs2=x{campos['rs2']}")

cpu.mostrar_resumo()
