"""
Testes automáticos da CPU RV32I + CTZ (Grupo 11).

Rodar a partir da raiz do repositório:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cpu import CPU


# -----------------------------------------------------------------------------
# Mini "montador": gera a palavra de 32 bits de cada formato (Figura 3 do PDF)
# -----------------------------------------------------------------------------
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


def tipo_u(imm20, rd, opcode):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | opcode


def tipo_j(imm, rd, opcode=0b1101111):
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) \
        | (((imm >> 12) & 0xFF) << 12) | (rd << 7) | opcode


def addi(rd, rs1, imm):
    return tipo_i(imm, rs1, 0b000, rd)


def ctz(rd, rs1):
    return tipo_i((0b0110000 << 5) | 0b00001, rs1, 0b001, rd)


class TestCPU(unittest.TestCase):
    def setUp(self):
        self.cpu = CPU()

    def rodar(self, *instrucoes):
        for inst in instrucoes:
            self.cpu.executar_ciclo(inst)

    def reg(self, n):
        return self.cpu.registradores[n]

    def reg_s(self, n):
        return CPU.para_com_sinal(self.cpu.registradores[n])

    # --- Registradores e PC ---------------------------------------------------
    def test_x0_sempre_zero(self):
        self.rodar(addi(0, 0, 123))
        self.assertEqual(self.reg(0), 0)

    def test_pc_avanca_4(self):
        self.rodar(addi(1, 0, 1), addi(1, 1, 1))
        self.assertEqual(self.cpu.pc, 8)

    # --- Tipo-R ---------------------------------------------------------------
    def test_tipo_r(self):
        self.rodar(addi(1, 0, -8), addi(2, 0, 3))
        casos = [
            (0b0000000, 0b000, -5),               # ADD
            (0b0100000, 0b000, -11),              # SUB
            (0b0000000, 0b001, -64),              # SLL
            (0b0000000, 0b010, 1),                # SLT  (-8 < 3)
            (0b0000000, 0b011, 0),                # SLTU (0xFFFFFFF8 < 3? não)
            (0b0000000, 0b100, -8 ^ 3),           # XOR
            (0b0000000, 0b101, 0xFFFFFFF8 >> 3),  # SRL
            (0b0100000, 0b101, -1),               # SRA
            (0b0000000, 0b110, -8 | 3),           # OR
            (0b0000000, 0b111, -8 & 3),           # AND
        ]
        for funct7, funct3, esperado in casos:
            with self.subTest(funct7=bin(funct7), funct3=bin(funct3)):
                self.rodar(tipo_r(funct7, 2, 1, funct3, 3))
                self.assertEqual(self.reg(3), esperado & 0xFFFFFFFF)

    # --- Tipo-I ---------------------------------------------------------------
    def test_tipo_i(self):
        self.rodar(addi(1, 0, -16))
        casos = [
            (addi(3, 1, 5), -11),
            (tipo_i(-1, 1, 0b010, 3), 1),                   # SLTI  (-16 < -1)
            (tipo_i(-1, 1, 0b011, 3), 1),                   # SLTIU (0xFFFFFFF0 < 0xFFFFFFFF)
            (tipo_i(0xFF, 1, 0b100, 3), -16 ^ 0xFF),        # XORI
            (tipo_i(0x0F, 1, 0b110, 3), -1),                # ORI
            (tipo_i(0xFF, 1, 0b111, 3), 0xF0),              # ANDI
            (tipo_i(4, 1, 0b001, 3), -256),                 # SLLI
            (tipo_i(4, 1, 0b101, 3), 0x0FFFFFFF),           # SRLI
            (tipo_i((0b0100000 << 5) | 4, 1, 0b101, 3), -1),  # SRAI
        ]
        for inst, esperado in casos:
            with self.subTest(inst=hex(inst)):
                self.rodar(inst)
                self.assertEqual(self.reg(3), esperado & 0xFFFFFFFF)

    # --- CTZ (Grupo 11) -------------------------------------------------------
    def test_ctz(self):
        for valor, esperado in [(80, 4), (1, 0), (0x400, 10), (-2048, 11)]:
            with self.subTest(valor=valor):
                self.cpu = CPU()
                self.rodar(addi(1, 0, valor), ctz(2, 1))
                self.assertEqual(self.reg(2), esperado)

    def test_ctz_zero_retorna_32(self):
        self.rodar(ctz(2, 0))
        self.assertEqual(self.reg(2), 32)

    def test_ctz_bit_31(self):
        self.rodar(tipo_u(0x80000, 1, 0b0110111), ctz(2, 1))  # LUI x1, 0x80000 -> 0x80000000
        self.assertEqual(self.reg(2), 31)

    # --- Memória --------------------------------------------------------------
    def test_sw_lw(self):
        self.rodar(addi(1, 0, 100), addi(2, 0, -7),
                   tipo_s(-4, 2, 1),                          # SW x2, -4(x1)
                   tipo_i(-4, 1, 0b010, 3, 0b0000011))        # LW x3, -4(x1)
        self.assertEqual(self.reg_s(3), -7)

    # --- Branches -------------------------------------------------------------
    def test_branches(self):
        # x1 = -1, x2 = 1
        casos = [
            (0b000, False), (0b001, True),   # BEQ, BNE
            (0b100, True), (0b101, False),   # BLT, BGE   (com sinal: -1 < 1)
            (0b110, False), (0b111, True),   # BLTU, BGEU (sem sinal: 0xFFFFFFFF > 1)
        ]
        for funct3, desvia in casos:
            with self.subTest(funct3=bin(funct3)):
                self.cpu = CPU()
                self.rodar(addi(1, 0, -1), addi(2, 0, 1), tipo_b(16, 2, 1, funct3))
                self.assertEqual(self.cpu.pc, 8 + 16 if desvia else 12)

    def test_branch_para_tras(self):
        self.cpu.pc = 40
        self.rodar(tipo_b(-24, 0, 0, 0b000))  # BEQ x0, x0, -24
        self.assertEqual(self.cpu.pc, 16)

    # --- Tipo-U ---------------------------------------------------------------
    def test_lui(self):
        self.rodar(tipo_u(0x12345, 1, 0b0110111))
        self.assertEqual(self.reg(1), 0x12345000)

    def test_lui_addi_monta_constante_32_bits(self):
        # Carregar 0x80000 (início da VRAM) em x1
        self.rodar(tipo_u(0x80, 1, 0b0110111), addi(1, 1, 0))
        self.assertEqual(self.reg(1), 0x80000)

    def test_auipc(self):
        self.cpu.pc = 0x100
        self.rodar(tipo_u(0x1, 1, 0b0010111))
        self.assertEqual(self.reg(1), 0x1100)

    # --- Tipo-J / JALR --------------------------------------------------------
    def test_jal(self):
        self.cpu.pc = 8
        self.rodar(tipo_j(20, 1))
        self.assertEqual(self.reg(1), 12)
        self.assertEqual(self.cpu.pc, 28)

    def test_jal_para_tras(self):
        self.cpu.pc = 100
        self.rodar(tipo_j(-40, 1))
        self.assertEqual(self.cpu.pc, 60)

    def test_jalr_retorno_de_funcao(self):
        self.rodar(addi(1, 0, 0x41))                   # endereço ímpar: bit 0 deve ser zerado
        self.rodar(tipo_i(4, 1, 0b000, 5, 0b1100111))  # JALR x5, 4(x1)
        self.assertEqual(self.cpu.pc, 0x44)
        self.assertEqual(self.reg(5), 8)

    def test_jalr_rd_igual_rs1(self):
        self.rodar(addi(1, 0, 32), tipo_i(0, 1, 0b000, 1, 0b1100111))  # JALR x1, 0(x1)
        self.assertEqual(self.cpu.pc, 32)
        self.assertEqual(self.reg(1), 8)


if __name__ == "__main__":
    unittest.main()