# src/simulador/instruction.py
# DEFINIÇÕES DE DECODIFICAÇÃO DE INSTRUÇÕES (PADRÃO 6-bit Opcode, 5-bit Registers)

# Opcode: Bits 31:26 (6 bits)
def get_opcode(ir):
    return (ir >> 26) & 0x3F

# Ra: Bits 25:21 (5 bits)
def get_ra(ir):
    return (ir >> 21) & 0x1F

# Rb: Bits 20:16 (5 bits)
def get_rb(ir):
    return (ir >> 16) & 0x1F

# Rc: Bits 15:11 (5 bits)
def get_rc(ir):
    # Para instruções R-Type ou para o terceiro registrador (bits 15:11)
    return (ir >> 11) & 0x1F

# Constante ou Imediato de 16 bits (bits 15:0)
def get_const16_high(ir):
    # Mantendo o nome para compatibilidade, mas representa a constante de 16 bits
    return ir & 0xFFFF

def get_const16_low(ir):
    # Mantendo o nome para compatibilidade, mas representa a constante de 16 bits
    return ir & 0xFFFF

# Endereço de Desvio de 26 bits (para J-Type)
def get_jump_address(ir):
    # Bits 25:0 (26 bits)
    return ir & 0x03FFFFFF