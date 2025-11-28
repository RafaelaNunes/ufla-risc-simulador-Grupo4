WORD_SIZE = 4

def read_mem(memory_list: list, address: int) -> int:
    index = address // WORD_SIZE
    if index < len(memory_list):
        return memory_list[index]
    return 0

def write_mem(memory_list: list, address: int, data: int):
    index = address // WORD_SIZE
    if index < len(memory_list):
        memory_list[index] = data

def print_memory_data(memory_list: list):
    print("--- Memória de Dados (Primeiras Palavras, Decimal) ---")
    for i in range(16):
        address = i * WORD_SIZE
        value = memory_list[i] if i < len(memory_list) else 0
        print(f"Endereço {address:<4}: {value}")