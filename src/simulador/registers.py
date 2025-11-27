# src/simulador/registers.py

def read_reg(registers_list: list, index: int) -> int:
    """Lê o valor de um registrador."""
    if index == 0: return 0
    return registers_list[index]

def write_reg(registers_list: list, index: int, data: int):
    """Escreve um valor no registrador (ignora R0)."""
    if index != 0:
        registers_list[index] = data

def print_registers(registers_list: list):
    """Imprime o estado dos registradores."""
    print("--- Banco de Registradores (Decimal) ---")
    registers_list[0] = 0 # Garante que R0 seja sempre zero
    
    for i in range(0, 32, 4):
        line = ""
        for j in range(4):
            idx = i + j
            if idx < 32:
                line += f"R{idx:02}: {registers_list[idx]:<10}"
        print(line.strip())