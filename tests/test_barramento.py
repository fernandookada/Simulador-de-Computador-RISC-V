"""
Testes do Barramento (dados, endereços e controle).

Rodar a partir da raiz do repositório:
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memoria import Memoria, ErroMemoria
from barramento import Barramento


class TestBarramento(unittest.TestCase):
    def setUp(self):
        self.memoria = Memoria()
        self.barramento = Barramento(self.memoria)

    def test_comeca_ocioso(self):
        self.assertEqual(self.barramento.controle, Barramento.NENHUM)
        self.assertEqual((self.barramento.leituras, self.barramento.escritas), (0, 0))

    def test_escrever_e_ler(self):
        self.barramento.escrever(0x400, 0xCAFEBABE)
        self.assertEqual(self.barramento.ler(0x400), 0xCAFEBABE)
        self.assertEqual(self.memoria.ler_palavra(0x400), 0xCAFEBABE)

    def test_estado_apos_escrita(self):
        self.barramento.escrever(0x80000, -1)
        self.assertEqual(self.barramento.enderecos, 0x80000)
        self.assertEqual(self.barramento.dados, 0xFFFFFFFF)  # mascarado em 32 bits
        self.assertEqual(self.barramento.controle, Barramento.NENHUM)

    def test_estado_apos_leitura(self):
        self.memoria.escrever_palavra(0x10, 0x12345678)
        self.barramento.escrever(0x20, 0xAAAA)
        valor = self.barramento.ler(0x10)
        self.assertEqual(valor, 0x12345678)
        self.assertEqual(self.barramento.enderecos, 0x10)
        self.assertEqual(self.barramento.dados, 0x12345678)
        self.assertEqual(self.barramento.controle, Barramento.NENHUM)

    def test_contadores(self):
        self.barramento.escrever(0x0, 1)
        self.barramento.escrever(0x4, 2)
        for _ in range(3):
            self.barramento.ler(0x0)
        self.assertEqual(self.barramento.escritas, 2)
        self.assertEqual(self.barramento.leituras, 3)

    def test_area_reservada_gera_erro_e_libera_controle(self):
        with self.assertRaises(ErroMemoria):
            self.barramento.escrever(0x90000, 1)
        self.assertEqual(self.barramento.controle, Barramento.NENHUM)

        with self.assertRaises(ErroMemoria):
            self.barramento.ler(0x90000)
        self.assertEqual(self.barramento.controle, Barramento.NENHUM)

        # Transações que falharam não entram nas métricas
        self.assertEqual((self.barramento.leituras, self.barramento.escritas), (0, 0))


if __name__ == "__main__":
    unittest.main()
