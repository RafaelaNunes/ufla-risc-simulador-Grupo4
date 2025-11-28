# exemplos/teste_jump_to_branch.asm
# Objetivo: JUMP (End. 20) -> BRANCH (End. 32) -> SUCESSO

# 0: Inicializa R1 = 5
ADDI R1, R0, 5
# 4: Inicializa R2 = 5
ADDI R2, R0, 5

# 8: O PULO DO GATO
# Pula direto para o endereço 20 (onde está o BEQ)
# Se falhar, vai executar a linha 12 e sujar R3 com 999
J 20

# 12: (Zona Morta - Não deve executar)
ADDI R3, R0, 999
# 16: (Zona Morta)
ADDI R3, R0, 888

# 20: (Alvo do Jump)
# Agora testa: Se R1 == R2 (5==5), vá para 32.
# Se falhar (não tomar o branch), executa a 24 e suja R3 com 777
BEQ R1, R2, 32

# 24: (Falha do Branch - Não deve executar)
ADDI R3, R0, 777
# 28: Pula para o fim (caso caia aqui por erro)
J 40

# 32: (Alvo do Branch - SUCESSO)
# Define R3 = 100 para provar que chegou aqui
ADDI R3, R0, 100

# 36: Fim
HALT

# 40: Fim alternativo
HALT