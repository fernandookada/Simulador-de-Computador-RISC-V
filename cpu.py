class CPU:
    def __init__(self):
        # Banco de 32 registradores (x0 até x31) e Program Counter (PC)
        self.registradores = [0] * 32
        self.pc = 0

    def definir_registrador(self, reg: int, valor: int):
        """Salva um valor de 32 bits no registrador, mantendo x0 sempre em 0."""
        if reg == 0:
            return
        self.registradores[reg] = valor & 0xFFFFFFFF

    def decodificar(self, instrucao: int) -> dict:
        """Extrai os campos da instrução de 32 bits usando operações bitwise."""
        return {
            "opcode": instrucao & 0b1111111,           # bits [6:0]
            "rd":     (instrucao >> 7) & 0b11111,      # bits [11:7]
            "funct3": (instrucao >> 12) & 0b111,       # bits [14:12]
            "rs1":    (instrucao >> 15) & 0b11111,     # bits [19:15]
            "rs2":    (instrucao >> 20) & 0b11111,     # bits [24:20]
            "funct7": (instrucao >> 25) & 0b1111111,   # bits [31:25]
        }

    def executar_ciclo(self, instrucao: int):
        """Decodifica a instrução, executa a operação básica na ULA e avança o PC."""
        campos = self.decodificar(instrucao)

        opcode = campos["opcode"]
        rd = campos["rd"]
        funct3 = campos["funct3"]
        val1 = self.registradores[campos["rs1"]]
        val2 = self.registradores[campos["rs2"]]
        funct7 = campos["funct7"]

        # Opcode 0110011 (51 / 0x33) -> Instruções do Tipo-R
        if opcode == 0b0110011:
            if funct3 == 0b000 and funct7 == 0b0000000:
                # ADD
                self.definir_registrador(rd, val1 + val2)
            elif funct3 == 0b000 and funct7 == 0b0100000:
                # SUB
                self.definir_registrador(rd, val1 - val2)
            elif funct3 == 0b111 and funct7 == 0b0000000:
                # AND
                self.definir_registrador(rd, val1 & val2)
            elif funct3 == 0b110 and funct7 == 0b0000000:
                # OR
                self.definir_registrador(rd, val1 | val2)

        # Avança o Program Counter para a próxima instrução (+4 bytes)
        self.pc += 4
        return campos

    def mostrar_resumo(self):
        """Exibe o PC atual e apenas os registradores que possuem valor diferente de 0."""
        print(f"\n--- Estado da CPU (PC = {self.pc}) ---")
        print(f"x0 = {self.registradores[0]} (constante zero)")
        for i in range(1, 32):
            if self.registradores[i] != 0:
                print(f"x{i} = {self.registradores[i]}")
