
ADDI R1, R0, 10      # R1 = 10 (Teste de Imediato Custom)
ADDI R2, R0, 5       # R2 = 5
ADD  R3, R1, R2      # R3 = 10 + 5 = 15 (Teste R-Type Padrão)
SUB  R4, R3, R2      # R4 = 15 - 5 = 10
SW   R4, R0          # Mem[10] = 10 (Teste de Store - Endereço base R4, offset 0 implícito na lógica SW)
HALT