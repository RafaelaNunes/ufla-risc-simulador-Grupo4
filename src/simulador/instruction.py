# src/simulador/instruction.py

def get_opcode(ir):
    return (ir >> 24) & 0xFF

def get_ra(ir):
    return (ir >> 16) & 0xFF

def get_rb(ir):
    return (ir >> 8) & 0xFF

def get_rc(ir):
    return ir & 0xFF

def get_const16_high(ir):
    return (ir >> 8) & 0xFFFF

def get_const16_low(ir):
    return ir & 0xFFFF

def get_jump_address(ir):
    return ir & 0xFFFFFF  # 24 bits para desvio
