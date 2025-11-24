

NUM_REGISTERS = 32

def create_registers():
    return [0] * NUM_REGISTERS

# registers.py (Exemplo de correção)

def read_reg(registers_list: list, index: int) -> int:
    """Lê o valor de um registrador, garantindo que R0 sempre retorna 0."""
    if index == 0:
        return 0
    # Adiciona verificação para evitar NoneType se o índice for inválido
    if 0 < index < len(registers_list):
        return registers_list[index]
    else:
        # Retorna 0 (ou levanta um erro, mas 0 é mais seguro para simulação)
        print(f"Aviso: Tentativa de ler registrador com índice inválido: {index}")
        return 0

def write_reg(registers: list, index: int, value: int):
    if index == 0:
        return
        
    if 0 < index < NUM_REGISTERS:
        registers[index] = value & 0xFFFFFFFF
    else:
        raise IndexError(f"Índice de registrador inválido para escrita: R{index}")

def print_registers(registers: list):
    print("--- Banco de Registradores (Decimal) ---")
    for i in range(0, NUM_REGISTERS, 4):
        line_parts = []
        for j in range(4):
            reg_index = i + j
            if reg_index < NUM_REGISTERS:
                line_parts.append(f"R{reg_index:02}: {registers[reg_index]:<10}")
        print("  ".join(line_parts))