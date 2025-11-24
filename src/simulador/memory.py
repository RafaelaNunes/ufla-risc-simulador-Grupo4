# memory.py

MEMORY_SIZE_WORDS = 65536  # 2^16 posições de palavra (palavra = 4 bytes)

def create_memory():
    """Cria a memória do processador como uma lista de inteiros (palavras de 32 bits)."""
    return [0] * MEMORY_SIZE_WORDS

def read_mem(memory: list, address: int) -> int:
    """
    Lê uma palavra (32 bits) no endereço de BYTE especificado.
    A memória é endereçada à palavra, então o endereço de byte é convertido.
    """
    # Checa se o endereço está alinhado à palavra (múltiplo de 4)
    if address % 4 != 0:
        raise ValueError(f"Endereço de memória não alinhado: {address}")

    word_index = address // 4
    if 0 <= word_index < MEMORY_SIZE_WORDS:
        return memory[word_index]
    raise IndexError(f"Endereço de memória fora do limite: {address}")

def write_mem(memory: list, address: int, value: int):
    """
    Escreve uma palavra (32 bits) no endereço de BYTE especificado.
    O valor deve ser tratado como um inteiro de 32 bits.
    """
    if address % 4 != 0:
        raise ValueError(f"Endereço de memória não alinhado: {address}")
        
    word_index = address // 4
    if 0 <= word_index < MEMORY_SIZE_WORDS:
        # Garante a aritmética de 32 bits
        memory[word_index] = value & 0xFFFFFFFF
    else:
        raise IndexError(f"Endereço de memória fora do limite para escrita: {address}")

def load_instruction_mem(memory: dict, address: int, binary_string: str):
    """
    Carrega a instrução binária em um dicionário de memória de instruções 
    (separada da memória de dados para simulação IF/MEM).
    """
    # Usaremos um dicionário separado para a Memória de Instruções (endereço -> binário)
    # Desta forma, mantemos a lista 'memory' apenas para dados.
    memory[address] = binary_string

def print_memory_data(memory: list):
    """Imprime as primeiras células da memória de dados usando apenas valores decimais."""
    print("--- Memória de Dados (Primeiras Palavras, Decimal) ---")
    # Imprime as primeiras 16 palavras (64 bytes)
    for i in range(0, 16): 
        address = i * 4
        value = memory[i]
        print(f"Endereço {address:<4}: {value}")