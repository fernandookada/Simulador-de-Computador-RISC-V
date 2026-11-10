class CPU:
    def __init__(self):
        # Banco de 32 registradores (x0 até x31) e Program Counter (PC)
        self.registradores = [0] * 32
        self.pc = 0
        # Estrutura simples de memória (endereço -> valor) para testar LW e SW
        self.memoria = {}

    def definir_registrador(self, reg: int, valor: int):
        """Salva um valor de 32 bits no registrador, mantendo x0 sempre em 0."""
        if reg == 0:
            return
        self.registradores[reg] = valor & 0xFFFFFFFF

    @staticmethod
    def para_com_sinal(valor: int) -> int:
        """Converte um valor de 32 bits para inteiro com sinal (complemento de 2)."""
        valor = valor & 0xFFFFFFFF
        if valor & (1 << 31):
            return valor - (1 << 32)
        return valor

    @staticmethod
    def estender_sinal(valor: int, qtd_bits: int) -> int:
        """Estende o bit de sinal (bit mais significativo) de um imediato."""
        bit_sinal = 1 << (qtd_bits - 1)
        if valor & bit_sinal:
            return valor - (1 << qtd_bits)
        return valor

    def decodificar(self, instrucao: int) -> dict:
        """
        Extrai os campos da instrução de 32 bits e monta os imediatos (Figura 3 do PDF).
        """
        opcode = instrucao & 0b1111111           # bits [6:0]
        rd     = (instrucao >> 7) & 0b11111      # bits [11:7]
        funct3 = (instrucao >> 12) & 0b111       # bits [14:12]
        rs1    = (instrucao >> 15) & 0b11111     # bits [19:15]
        rs2    = (instrucao >> 20) & 0b11111     # bits [24:20]
        funct7 = (instrucao >> 25) & 0b1111111   # bits [31:25]

        # Imediato Tipo-I: bits [31:20] (12 bits)
        imm_i = self.estender_sinal((instrucao >> 20) & 0xFFF, 12)

        # Imediato Tipo-S: junta bits [31:25] (imm[11:5]) com bits [11:7] (imm[4:0])
        imm_s_bits = (funct7 << 5) | rd
        imm_s = self.estender_sinal(imm_s_bits, 12)

        # Imediato Tipo-B: junta imm[12] (bit 31), imm[11] (bit 7), imm[10:5] (bits 30:25), imm[4:1] (bits 11:8)
        bit_12   = (instrucao >> 31) & 0b1
        bit_11   = (instrucao >> 7) & 0b1
        bits_10_5 = (instrucao >> 25) & 0b111111
        bits_4_1  = (instrucao >> 8) & 0b1111
        imm_b_bits = (bit_12 << 12) | (bit_11 << 11) | (bits_10_5 << 5) | (bits_4_1 << 1)
        imm_b = self.estender_sinal(imm_b_bits, 13)

        # Imediato Tipo-U: bits [31:12] já posicionados nos 20 bits superiores
        imm_u = instrucao & 0xFFFFF000

        # Imediato Tipo-J: junta imm[20] (bit 31), imm[10:1] (bits 30:21), imm[11] (bit 20), imm[19:12] (bits 19:12)
        bit_20     = (instrucao >> 31) & 0b1
        bits_10_1  = (instrucao >> 21) & 0b1111111111
        bit_11_j   = (instrucao >> 20) & 0b1
        bits_19_12 = (instrucao >> 12) & 0b11111111
        imm_j_bits = (bit_20 << 20) | (bits_19_12 << 12) | (bit_11_j << 11) | (bits_10_1 << 1)
        imm_j = self.estender_sinal(imm_j_bits, 21)

        return {
            "opcode": opcode,
            "rd":     rd,
            "funct3": funct3,
            "rs1":    rs1,
            "rs2":    rs2,
            "funct7": funct7,
            "imm_i":  imm_i,
            "imm_s":  imm_s,
            "imm_b":  imm_b,
            "imm_u":  imm_u,
            "imm_j":  imm_j,
        }

    def executar_ciclo(self, instrucao: int) -> dict:
        """Decodifica a instrução, executa na ULA/Memória e atualiza o PC."""
        c = self.decodificar(instrucao)

        opcode = c["opcode"]
        rd     = c["rd"]
        funct3 = c["funct3"]
        funct7 = c["funct7"]

        # Valores dos registradores fonte (sem sinal e com sinal)
        u_rs1 = self.registradores[c["rs1"]]
        u_rs2 = self.registradores[c["rs2"]]
        s_rs1 = self.para_com_sinal(u_rs1)
        s_rs2 = self.para_com_sinal(u_rs2)

        proximo_pc = self.pc + 4

        # ---------------------------------------------------------------------
        # 1. Aritméticas e Lógicas (Tipo-R) -> opcode = 0110011
        # ---------------------------------------------------------------------
        if opcode == 0b0110011:
            shamt = u_rs2 & 0b11111
            if funct3 == 0b000 and funct7 == 0b0000000:    # ADD
                self.definir_registrador(rd, u_rs1 + u_rs2)
            elif funct3 == 0b000 and funct7 == 0b0100000:  # SUB
                self.definir_registrador(rd, u_rs1 - u_rs2)
            elif funct3 == 0b001 and funct7 == 0b0000000:  # SLL
                self.definir_registrador(rd, u_rs1 << shamt)
            elif funct3 == 0b010 and funct7 == 0b0000000:  # SLT (com sinal)
                self.definir_registrador(rd, 1 if s_rs1 < s_rs2 else 0)
            elif funct3 == 0b011 and funct7 == 0b0000000:  # SLTU (sem sinal)
                self.definir_registrador(rd, 1 if u_rs1 < u_rs2 else 0)
            elif funct3 == 0b100 and funct7 == 0b0000000:  # XOR
                self.definir_registrador(rd, u_rs1 ^ u_rs2)
            elif funct3 == 0b101 and funct7 == 0b0000000:  # SRL (lógico)
                self.definir_registrador(rd, u_rs1 >> shamt)
            elif funct3 == 0b101 and funct7 == 0b0100000:  # SRA (aritmético)
                self.definir_registrador(rd, s_rs1 >> shamt)
            elif funct3 == 0b110 and funct7 == 0b0000000:  # OR
                self.definir_registrador(rd, u_rs1 | u_rs2)
            elif funct3 == 0b111 and funct7 == 0b0000000:  # AND
                self.definir_registrador(rd, u_rs1 & u_rs2)

        # ---------------------------------------------------------------------
        # 2. Aritméticas e Lógicas com Imediato (Tipo-I) -> opcode = 0010011
        # ---------------------------------------------------------------------
        elif opcode == 0b0010011:
            imm = c["imm_i"]
            u_imm = imm & 0xFFFFFFFF
            shamt = c["rs2"]  # Nos shifts com imediato, os bits [24:20] são o shamt

            if funct3 == 0b000:                            # ADDI
                self.definir_registrador(rd, s_rs1 + imm)
            elif funct3 == 0b010:                          # SLTI (com sinal)
                self.definir_registrador(rd, 1 if s_rs1 < imm else 0)
            elif funct3 == 0b011:                          # SLTIU (sem sinal)
                self.definir_registrador(rd, 1 if u_rs1 < u_imm else 0)
            elif funct3 == 0b100:                          # XORI
                self.definir_registrador(rd, u_rs1 ^ u_imm)
            elif funct3 == 0b110:                          # ORI
                self.definir_registrador(rd, u_rs1 | u_imm)
            elif funct3 == 0b111:                          # ANDI
                self.definir_registrador(rd, u_rs1 & u_imm)
            elif funct3 == 0b001 and funct7 == 0b0000000:  # SLLI
                self.definir_registrador(rd, u_rs1 << shamt)
            elif funct3 == 0b101 and funct7 == 0b0000000:  # SRLI
                self.definir_registrador(rd, u_rs1 >> shamt)
            elif funct3 == 0b101 and funct7 == 0b0100000:  # SRAI
                self.definir_registrador(rd, s_rs1 >> shamt)
            elif funct3 == 0b001 and funct7 == 0b0110000 and shamt == 0b00001:  # CTZ (Grupo 11)
                if u_rs1 == 0:
                    zeros = 32
                else:
                    zeros = 0
                    temp = u_rs1
                    while (temp & 1) == 0:
                        zeros += 1
                        temp >>= 1
                self.definir_registrador(rd, zeros)

        # ---------------------------------------------------------------------
        # 3. Acesso à Memória: LW (Tipo-I: 0000011) e SW (Tipo-S: 0100011)
        # ---------------------------------------------------------------------
        elif opcode == 0b0000011:
            if funct3 == 0b010:  # LW (Load Word): rd = MEM[rs1 + imm_i]
                endereco = (s_rs1 + c["imm_i"]) & 0xFFFFFFFF
                valor_lido = self.memoria.get(endereco, 0)
                self.definir_registrador(rd, valor_lido)

        elif opcode == 0b0100011:
            if funct3 == 0b010:  # SW (Store Word): MEM[rs1 + imm_s] = rs2
                endereco = (s_rs1 + c["imm_s"]) & 0xFFFFFFFF
                self.memoria[endereco] = u_rs2

        # ---------------------------------------------------------------------
        # 4. Desvio Condicional (Branch - Tipo-B) -> opcode = 1100011
        # ---------------------------------------------------------------------
        elif opcode == 0b1100011:
            desviar = False
            if funct3 == 0b000:    # BEQ (igual)
                desviar = (u_rs1 == u_rs2)
            elif funct3 == 0b001:  # BNE (diferente)
                desviar = (u_rs1 != u_rs2)
            elif funct3 == 0b100:  # BLT (menor com sinal)
                desviar = (s_rs1 < s_rs2)
            elif funct3 == 0b101:  # BGE (maior ou igual com sinal)
                desviar = (s_rs1 >= s_rs2)
            elif funct3 == 0b110:  # BLTU (menor sem sinal)
                desviar = (u_rs1 < u_rs2)
            elif funct3 == 0b111:  # BGEU (maior ou igual sem sinal)
                desviar = (u_rs1 >= u_rs2)

            if desviar:
                proximo_pc = self.pc + c["imm_b"]

        # ---------------------------------------------------------------------
        # 5. Tipo-U: LUI (0110111) e AUIPC (0010111)
        # ---------------------------------------------------------------------
        elif opcode == 0b0110111:  # LUI: rd = imm << 12
            self.definir_registrador(rd, c["imm_u"])

        elif opcode == 0b0010111:  # AUIPC: rd = PC + (imm << 12)
            self.definir_registrador(rd, self.pc + c["imm_u"])

        # ---------------------------------------------------------------------
        # 6. Saltos incondicionais: JAL (Tipo-J: 1101111) e JALR (Tipo-I: 1100111)
        # ---------------------------------------------------------------------
        elif opcode == 0b1101111:  # JAL: rd = PC + 4; PC = PC + imm_j
            self.definir_registrador(rd, self.pc + 4)
            proximo_pc = self.pc + c["imm_j"]

        elif opcode == 0b1100111 and funct3 == 0b000:  # JALR: rd = PC + 4; PC = (rs1 + imm_i) & ~1
            # O destino é calculado antes de escrever rd (caso rd == rs1)
            destino = (s_rs1 + c["imm_i"]) & ~1
            self.definir_registrador(rd, self.pc + 4)
            proximo_pc = destino

        self.pc = proximo_pc & 0xFFFFFFFF
        return c

    def mostrar_resumo(self):
        """Exibe o PC atual, os registradores alterados e as posições de memória usadas."""
        print(f"\n--- Estado da CPU (PC = {self.pc}) ---")
        print(f"x0 = {self.registradores[0]} (constante zero)")
        for i in range(1, 32):
            if self.registradores[i] != 0:
                val_sinal = self.para_com_sinal(self.registradores[i])
                print(f"x{i} = {val_sinal} (hex: 0x{self.registradores[i]:08X})")

        if self.memoria:
            print("\n--- Posições de Memória Utilizadas ---")
            for end, val in self.memoria.items():
                print(f"MEM[0x{end:05X}] = {self.para_com_sinal(val)} (hex: 0x{val:08X})")