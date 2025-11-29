ADDI R1, R0, 3
ADDI R2, R0, 9
JEQ  R1, R2, LABEL   # não desvia

ADDI R3, R0, 100      # deve executar

J   NEXT              # desvia

LABEL:
ADDI R3, R0, 999      # NÃO deve executar

NEXT:
ADDI R4, R3, 1
HALT
