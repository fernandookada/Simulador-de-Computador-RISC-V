"""
Testes de integração: programas carregados na memória e executados pelo Simulador
(CPU -> Barramento -> Memória).

Rodar a partir da raiz do repositório:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from memoria import ErroMemoria
from simulador import Simulador

# Reaproveita o mini "montador" de test_cpu.py. O módulo é importado inteiro
# (e não com "from ... import") para a classe TestCPU não ser executada duas vezes.
import test_cpu as m

OP_LUI = 0b0110111
OP_LW = 0b0000011
OP_JALR = 0b1100111


def lw(rd, rs1, imm):
    return m.tipo_i(imm, rs1, 0b010, rd, OP_LW)


def sw(rs2, rs1, imm):
    return m.tipo_s(imm, rs2, rs1)


def lui(rd, imm20):
    return m.tipo_u(imm20, rd, OP_LUI)


class TestIntegracao(unittest.TestCase):
    def setUp(self):
        self.sim = Simulador()

    def reg(self, n):
        return self.sim.cpu.registradores[n]

    def rodar(self, programa, **kwargs):
        self.sim.carregar(programa)
        return self.sim.executar(**kwargs)

    # --- Busca de instruções --------------------------------------------------
    def test_busca_da_memoria_e_pc_avanca_4(self):
        self.sim.carregar([m.addi(1, 0, 5), m.addi(2, 1, 3), m.addi(3, 2, 1)])
        pcs = []
        for _ in range(3):
            self.sim.cpu.passo()
            pcs.append(self.sim.cpu.pc)
        self.assertEqual(pcs, [4, 8, 12])
        self.assertEqual((self.reg(1), self.reg(2), self.reg(3)), (5, 8, 9))

    def test_carregar_em_outro_endereco(self):
        self.sim.carregar([m.addi(1, 0, 7)], endereco_inicial=0x1000)
        self.assertEqual(self.sim.cpu.pc, 0x1000)
        self.assertEqual(self.sim.executar(), 1)
        self.assertEqual(self.reg(1), 7)

    # --- Halt -----------------------------------------------------------------
    def test_halt_em_instrucao_zero(self):
        executadas = self.rodar([m.addi(1, 0, 1), m.addi(1, 1, 1), m.addi(1, 1, 1)])
        self.assertEqual(executadas, 3)
        self.assertEqual(self.sim.cpu.pc, 12)  # parou no endereço vazio, sem executá-lo
        self.assertEqual(self.reg(1), 3)

    # --- Laço com branch para trás --------------------------------------------
    def test_laco_soma_1_a_10(self):
        programa = [
            m.addi(1, 0, 0),                  # 0x00: x1 = 0  (soma)
            m.addi(2, 0, 1),                  # 0x04: x2 = 1  (i)
            m.addi(3, 0, 11),                 # 0x08: x3 = 11 (limite)
            m.tipo_r(0, 2, 1, 0b000, 1),      # 0x0C: ADD x1, x1, x2
            m.addi(2, 2, 1),                  # 0x10: x2 = x2 + 1
            m.tipo_b(-8, 3, 2, 0b001),        # 0x14: BNE x2, x3, -8 (volta para 0x0C)
        ]
        executadas = self.rodar(programa)
        self.assertEqual(self.reg(1), 55)
        self.assertEqual(executadas, 3 + 3 * 10)

    # --- Memória de dados -----------------------------------------------------
    def test_sw_lw_na_ram(self):
        programa = [
            m.addi(1, 0, -7),   # x1 = -7
            sw(1, 0, 0x400),    # SW x1, 0x400(x0)
            lw(2, 0, 0x400),    # LW x2, 0x400(x0)
        ]
        self.rodar(programa)
        self.assertEqual(self.reg(2), (-7) & 0xFFFFFFFF)
        self.assertEqual(self.sim.memoria.ler_palavra(0x400), (-7) & 0xFFFFFFFF)
        # 4 buscas (3 instruções + halt) + 1 LW; 1 escrita (SW)
        self.assertEqual(self.sim.barramento.leituras, 5)
        self.assertEqual(self.sim.barramento.escritas, 1)

    def test_escrita_na_vram(self):
        programa = [
            lui(1, 0x80),          # LUI  x1, 0x80      -> x1 = 0x80000 (início da VRAM)
            m.addi(2, 0, 72),      # ADDI x2, x0, 72    -> 'H'
            sw(2, 1, 0),           # SW   x2, 0(x1)
        ]
        self.rodar(programa)
        self.assertEqual(self.sim.memoria.ler_vram()[0], ord("H"))
        self.assertEqual(self.sim.memoria.ler_vram_ascii(), "H")

    def test_es_programada_vram_a_cada_n_instrucoes(self):
        programa = [
            lui(1, 0x80),          # 1. x1 = 0x80000 (VRAM)
            m.addi(2, 0, ord("O")),# 2. x2 = 'O'
            sw(2, 1, 0),           # 3. VRAM[0x80000] = 'O'  -> 1ª transmissão (ciclo 3): "O"
            m.addi(2, 0, ord("I")),# 4. x2 = 'I'
            sw(2, 1, 4),           # 5. VRAM[0x80004] = 'I'
            m.addi(3, 0, 1),       # 6. x3 = 1               -> 2ª transmissão (ciclo 6): "OI"
        ]
        executadas = self.rodar(programa, intervalo_vram=3, imprimir_vram=False)
        self.assertEqual(executadas, 6)
        self.assertEqual(self.sim.transmissoes_vram, [(3, "O"), (6, "OI")])

    # --- Chamada de função ----------------------------------------------------
    def test_jal_jalr_chamada_de_funcao(self):
        programa = [
            m.addi(10, 0, 5),                     # 0x00: x10 = 5 (argumento)
            m.tipo_j(12, 1),                      # 0x04: JAL x1, +12 -> função em 0x10
            m.addi(11, 10, 0),                    # 0x08: x11 = x10 (retorno da função)
            m.tipo_j(12, 0),                      # 0x0C: JAL x0, +12 -> 0x18 (halt)
            m.tipo_r(0, 10, 10, 0b000, 10),       # 0x10: função: ADD x10, x10, x10
            m.tipo_i(0, 1, 0b000, 0, OP_JALR),    # 0x14: JALR x0, 0(x1) -> retorna para 0x08
        ]
        executadas = self.rodar(programa)
        self.assertEqual(self.reg(11), 10)
        self.assertEqual(self.reg(1), 0x08)
        self.assertEqual(executadas, 6)
        self.assertEqual(self.sim.cpu.pc, 0x18)

    # --- CTZ (Grupo 11) -------------------------------------------------------
    def test_ctz_da_memoria(self):
        self.rodar([m.addi(1, 0, 0x400), m.ctz(2, 1)])
        self.assertEqual(self.reg(2), 10)

    # --- Erros ----------------------------------------------------------------
    def test_sw_na_area_reservada(self):
        programa = [
            lui(1, 0x90),        # x1 = 0x90000 (área reservada)
            sw(0, 1, 0),         # SW x0, 0(x1)
        ]
        with self.assertRaises(ErroMemoria):
            self.rodar(programa)

    def test_opcode_desconhecido(self):
        with self.assertRaises(ValueError):
            self.rodar([0xFFFFFFFF])

    def test_max_ciclos_interrompe_laco_infinito(self):
        executadas = self.rodar([m.tipo_b(0, 0, 0, 0b000)], max_ciclos=50)  # BEQ x0, x0, 0
        self.assertEqual(executadas, 50)
        self.assertEqual(self.sim.cpu.pc, 0)


if __name__ == "__main__":
    unittest.main()
