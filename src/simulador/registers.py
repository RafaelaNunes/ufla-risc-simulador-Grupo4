# registers.py

NUM_REGISTERS = 32

def create_registers():
    """Cria os 32 registradores (todos inicializados com zero). Retorna uma lista."""
    # O registrador R0 é implicitamente zero aqui, mas a lógica de escrita em R0 
    # deve ser tratada no seu simulador principal.
    return [0] * NUM_REGISTERS

def read_reg(registers: list, index: int) -> int:
    """Lê o valor de um registrador pelo seu índice (0-31)."""
    if 0 <= index < NUM_REGISTERS:
        return registers[index]
    raise IndexError(f"Índice de registrador inválido: R{index}")

def write_reg(registers: list, index: int, value: int):
    """
    Escreve um valor em um registrador pelo seu índice (1-31).
    Garante que o valor seja tratado como um inteiro de 32 bits (andando com 0xFFFFFFFF).
    R0 não deve ser escrito (tratado pelo chamador).
    """
    if index == 0:
        # Ignora a escrita em R0 (Hardwired Zero)
        return
        
    if 0 < index < NUM_REGISTERS:
        # Garante a aritmética de 32 bits (usa decimais, mas com o limite de 32 bits)
        registers[index] = value & 0xFFFFFFFF
    else:
        raise IndexError(f"Índice de registrador inválido para escrita: R{index}")

def print_registers(registers: list):
    """Imprime o estado dos registradores usando apenas valores decimais."""
    print("--- Banco de Registradores (Decimal) ---")
    for i in range(0, NUM_REGISTERS, 4):
        line_parts = []
        for j in range(4):
            reg_index = i + j
            if reg_index < NUM_REGISTERS:
                line_parts.append(f"R{reg_index:02}: {registers[reg_index]:<10}")
        print("  ".join(line_parts))