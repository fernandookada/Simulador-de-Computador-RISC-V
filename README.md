# Plano de Desenvolvimento: Simulador RISC-V

**Grupo:** 11 (Instrução Especial Exclusiva: CTZ) **Stack Tecnológica:** Python (Arquitetura Orientada a Objetos)

**Integrantes:** Anderson Freitas, Fernando Costa.

**Repositório:** LINK

## 1\. Arquitetura do Sistema (Classes do Python)

A estrutura do projeto será dividida em módulos que representam o hardware do computador.

### `Classe Memoria`

* Atuará como a estrutura principal de armazenamento (dicionário ou array).  
* **Mapeamento de Endereços:**  
  * `0x00000` a `0x7FFFF`: **RAM Principal** (onde ficarão o código do programa de teste, dados e pilha).  
  * `0x80000` a `0x8FFFF`: **VRAM** (memória de vídeo).  
  * `0x9FC00` a `0x9FFFF`: **Periféricos** (Hardware Mapeado).

### `Classe Barramento`

* Ponte de controle e comunicação entre a CPU e a Memória.  
* **Atributos essenciais:**  
  * `dados` (32 bits).  
  * `enderecos` (32 bits).  
  * `controle` (sinaliza permissão de leitura ou escrita).

### `Classe CPU`

* **Registradores:** Array/Lista de 32 posições (`x0` a `x31`). O registrador `x0` será mantido com valor constante `0`.  
* **PC (Program Counter):** Ponteiro/variável que indica o endereço de memória da instrução atual.  
* **Decodificador:** Lógica para ler os 32 bits vindos da memória e realizar *bitwise* para extrair o `opcode` (bits \[6:0\]), `rs1`, `rs2`, `rd`, `funct3` e `funct7`.  
* **Instrução Grupo 11:** Implementação da função específica **CTZ** (Count Trailing Zeros).

### `Classe Simulador` (Main)

* Módulo agregador que instanciará a `Memoria`, o `Barramento` e a `CPU`.  
* Responsável pelo loop infinito de *Busca*, *Decodificação* e *Execução*.  
* Responsável por ler a VRAM a cada *n* ciclos e dar um `print()` dos caracteres na tela do terminal.

---

## 2\. Cronograma de Desenvolvimento (6 Semanas)

| Semana | Etapa | Meta Prática |
| :---- | :---- | :---- |
| **Semana 1** | Esboço e Planejamento | Criar repositório, definir papéis no grupo, montar estrutura de arquivos e criar os esqueletos das Classes. |
| **Semana 2** | Início da CPU | Implementar os 32 registradores, o Program Counter (PC) e a extração do `opcode`. |
| **Semana 3** | Conclusão da CPU | Implementar as lógicas da ULA (Tipos R, I, S, B, U, J) e a instrução **CTZ**. |
| **Semana 4** | Memória RAM | Construir a lógica de leitura/escrita e bloquear as faixas hexadecimais de memória. |
| **Semana 5** | Barramento | Conectar a `CPU` à `Memoria` e gerenciar o tráfego dos dados. |
| **Semana 6** | E/S e Testes Finais | Fazer o output da VRAM no terminal (ASCII) e rodar o programa de teste traduzido para RISC-V. |

---

## 3\. Tarefas Extras (Opcional \- Para bônus de nota)

Se o cronograma principal for finalizado com folga, o grupo focará em:

1. **Memória Cache:** Criar uma classe Cache de 256 linhas entre o Barramento e a CPU.  
2. **Interface Gráfica:** Substituir o print no terminal por uma janela iterativa usando `Tkinter` ou `Pygame`.  
3. **Interrupção Externa:** Adicionar "listener" para interrupções disparadas pelo teclado.