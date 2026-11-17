"""
Testes da Memória (RAM, VRAM, área reservada e periféricos).

Rodar a partir da raiz do repositório:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memoria import Memoria, ErroMemoria


class TestMemoria(unittest.TestCase):
    def setUp(self):
        self.mem = Memoria()

    # --- Mapeamento de regiões -----------------------------------------------
    def test_regioes_nos_limites(self):
        casos = [
            (0x00000, "RAM"), (0x7FFFF, "RAM"),
            (0x80000, "VRAM"), (0x8FFFF, "VRAM"),
            (0x90000, "RESERVADA"), (0x9FBFF, "RESERVADA"),
            (0x9FC00, "PERIFERICOS"), (0x9FFFF, "PERIFERICOS"),
        ]
        for endereco, esperado in casos:
            with self.subTest(endereco=hex(endereco)):
                self.assertEqual(self.mem.regiao(endereco), esperado)

    def test_memoria_comeca_zerada(self):
        self.assertEqual(self.mem.ler_palavra(0x100), 0)
        self.assertEqual(self.mem.ler_palavra(0x80000), 0)

    # --- Leitura e escrita ----------------------------------------------------
    def test_escrever_e_ler_palavra_em_cada_regiao_permitida(self):
        for endereco in (0x00000, 0x7FFFC, 0x80000, 0x8FFFC, 0x9FC00, 0x9FFFC):
            with self.subTest(endereco=hex(endereco)):
                self.mem.escrever_palavra(endereco, 0xDEADBEEF)
                self.assertEqual(self.mem.ler_palavra(endereco), 0xDEADBEEF)

    def test_little_endian(self):
        self.mem.escrever_palavra(0x10, 0x11223344)
        self.assertEqual([self.mem.ler_byte(0x10 + i) for i in range(4)], [0x44, 0x33, 0x22, 0x11])

    def test_bytes_formam_palavra(self):
        for i, b in enumerate([0x78, 0x56, 0x34, 0x12]):
            self.mem.escrever_byte(0x20 + i, b)
        self.assertEqual(self.mem.ler_palavra(0x20), 0x12345678)

    def test_valor_negativo_vira_32_bits(self):
        self.mem.escrever_palavra(0x0, -1)
        self.assertEqual(self.mem.ler_palavra(0x0), 0xFFFFFFFF)

    def test_palavras_vizinhas_nao_se_sobrescrevem(self):
        self.mem.escrever_palavra(0x0, 0xAAAAAAAA)
        self.mem.escrever_palavra(0x4, 0xBBBBBBBB)
        self.assertEqual(self.mem.ler_palavra(0x0), 0xAAAAAAAA)
        self.assertEqual(self.mem.ler_palavra(0x4), 0xBBBBBBBB)

    # --- Bloqueios ------------------------------------------------------------
    def test_area_reservada_bloqueada(self):
        for endereco in (0x90000, 0x95000, 0x9FBFC):
            with self.subTest(endereco=hex(endereco)):
                with self.assertRaises(ErroMemoria):
                    self.mem.escrever_palavra(endereco, 1)
                with self.assertRaises(ErroMemoria):
                    self.mem.ler_palavra(endereco)
                with self.assertRaises(ErroMemoria):
                    self.mem.ler_byte(endereco)

    def test_fora_do_mapa(self):
        for endereco in (0xA0000, 0xFFFFFFFC, -4):
            with self.subTest(endereco=endereco):
                with self.assertRaises(ErroMemoria):
                    self.mem.ler_palavra(endereco)

    def test_acesso_desalinhado(self):
        with self.assertRaises(ErroMemoria):
            self.mem.escrever_palavra(0x2, 1)
        with self.assertRaises(ErroMemoria):
            self.mem.ler_palavra(0x80001)

    # --- Utilitários ----------------------------------------------------------
    def test_carregar_programa(self):
        programa = [0x00A00093, 0x00500113, 0x002081B3]
        self.mem.carregar_programa(programa)
        self.assertEqual([self.mem.ler_palavra(4 * i) for i in range(3)], programa)

    def test_ler_vram(self):
        for i, letra in enumerate(b"OI"):
            self.mem.escrever_byte(Memoria.INICIO_VRAM + i, letra)
        vram = self.mem.ler_vram()
        self.assertEqual(len(vram), 0x10000)
        self.assertEqual(vram[:2], b"OI")


if __name__ == "__main__":
    unittest.main()
