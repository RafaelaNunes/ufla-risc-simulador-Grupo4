# Simulador Funcional do Processador UFLA-RISC

Este projeto implementa um simulador funcional para o processador RISC de 32 bits **UFLA-RISC**, desenvolvido para a disciplina de Arquitetura de Computadores II (GCC123)

O simulador executa instruções binárias em um pipeline de 4 estágios (IF, ID, EX/MEM, WB), com suporte a detecção de _hazards_ de dados (resolvidos via Forwarding e Stalls) e de controle.

## Integrantes do Grupo

- Davi Gomides
- Eduardo Oliveira
- João Lucas Ramalho
- Luan Yudi
- Rafaela Valadão

## Estrutura do Projeto

A organização segue as diretrizes do trabalho:

- `src/`: Código fonte do simulador e interpretador (Assembler).
- `binarios/`: Arquivos `.bin` e `.txt` gerados automaticamente pelo montador.
- `exemplos/`: Códigos em Assembly (`.asm`) para teste.
- `docs/`: Documentação adicional.

## Instruções Adicionais Implementadas

Além do conjunto base (22 instruções), foram implementadas as seguintes instruções extras para facilitar o desenvolvimento:

1.  **R-Type:** `MUL`, `DIV`, `NOR`.
2.  **I-Type (Imediatos):** `ADDI`, `SUBI`, `MULI`, `ANDI`, `SLTI`.

## Como Executar

### Pré-requisitos

- Python 3.x instalado.

### 1. Clonar o repositório

```bash
git clone [https://github.com/usuario/ufla-risc-simulador-Grupo4.git](https://github.com/usuario/ufla-risc-simulador-Grupo4.git)
cd ufla-risc-simulador-Grupo4
2. Executar o Simulador
O projeto possui um montador integrado que converte automaticamente os arquivos .asm da pasta exemplos para binário antes da execução.

Opção A: Menu Interativo (Recomendado) Execute sem argumentos para visualizar a lista de testes disponíveis:

Bash

python3 -m src.simulador.main
Opção B: Executar um arquivo específico Passe o caminho do arquivo Assembly como argumento:

Bash

python3 -m src.simulador.main exemplos/teste_hazard.asm
Testes Realizados
Os testes cobrem aritmética básica, acesso à memória e resolução de conflitos de pipeline . Os arquivos fonte estão na pasta exemplos/:

teste_basico.asm: Soma e subtração básica.

teste_mul.asm: Multiplicação e divisão.

teste_memoria.asm: Leitura e escrita (LW/SW) e manipulação de endereços.

teste_hazards.asm: Teste complexo de Forwarding, Stalls (Load-Use) e Jumps.

teste_jump_to_branch.asm: Teste de fluxo de controle (Jump seguido de Branch).

teste_hazard_dados: Teste de Forwarding (adiantamento).

teste_hazard_controle: Teste de fluxo de controle .

Para rodar a bateria de testes, utilize o menu interativo descrito acima.

Licença
Projeto acadêmico sem licença comercial.
```
