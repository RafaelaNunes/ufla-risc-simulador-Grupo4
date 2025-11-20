# Teste completo UFLA-RISC
# enderecamento inicial
address 0000000000000000

# 1) Constantes: montar r1 = 10, r2 = 3
lclh r1 0
lcll r1 10

lclh r2 0
lcll r2 3

# 2) Operações aritméticas e lógicas
# r3 = r1 + r2  (ADD)
add r1 r2 r3

# r4 = r2 - r1  (SUB)
sub r2 r1 r4

# r5 = r1 & r2  (AND)
and r1 r2 r5

# r6 = r1 | r2  (OR)
or r1 r2 r6

# r7 = r1 ^ r2  (XOR)
xor r1 r2 r7

# 3) Shifts (usar r3 and r2 as valores)
# r8 = r3 << (r2)
lsl r3 r2 r8

# r9 = r3 >> (r2)  (logical)
lsr r3 r2 r9

# r10 = arithmetic right
asr r3 r2 r10

# r11 = arithmetic left (same as lsl)
asl r3 r2 r11

# 4) Memória: store and load
# preparar endereço em r12 = 5 e valor em r13 = 1234
lclh r12 0
lcll r12 5

lclh r13 0
lcll r13 1234

# store r13 into memory at address r12: memoria[r12] = r13
store r12 r13

# load from memory[r12] into r14
load r14 r12

# 5) Branches & jumps
# set r15 = 0, r16 = 0 ; beq r15 r16 -> should jump to LABEL_EQ
lclh r15 0
lcll r15 0

lclh r16 0
lcll r16 0

# this BEQ should be taken (r15==r16)
beq r15 r16 LABEL_EQ

# if branch not taken (should not execute)
lclh r17 0
lcll r17 77

# LABEL_EQ:
LABEL_EQ:
# inside label we set r17 = 999
lclh r17 0
lcll r17 999

# 6) Subroutine: jal / jr
# call subroutine SUBR which will set r18 = 42 and return
jal SUBR

# after return, r31 contains return address; we can test jr by jumping to it (optional)
# SUBR:
SUBR:
# set r18 = 42
lclh r18 0
lcll r18 42
# return: jr r31
jr r31

# 7) Test BNE: set r19=1, r20=2 -> bne should jump to LABEL_BNE
lclh r19 0
lcll r19 1
lclh r20 0
lcll r20 2

bne r19 r20 LABEL_BNE

# fallthrough (if not jumped, set r21 = 111)
lclh r21 0
lcll r21 111

LABEL_BNE:
# set r22 = 222
lclh r22 0
lcll r22 222

# 8) jump unconditional (j) to END
j END

# unreachable code - should be skipped
lclh r23 0
lcll r23 9999

END:
# final register touch to mark end
lclh r31 0
lcll r31 777

# NOTE: assembler may not support a 'halt' mnemonic. If it doesn't, append the HALT line
# manually to the generated binary file:
# 11111111111111111111111111111111

# EOF
