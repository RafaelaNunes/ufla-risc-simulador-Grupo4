# src/simulador/registers.py

NUM_REGISTERS = 32

def create_registers():
    """Cria os 32 registradores (todos inicializados com zero)."""
    return [0] * NUM_REGISTERS

def read_reg(registers, index):
    return registers[index]

def write_reg(registers, index, value):
    registers[index] = value & 0xFFFFFFFF  # garante 32 bits
