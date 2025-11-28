# src/simulador/instruction.py

# ==============================================================================
# Funções de Conversão e Auxiliares
# ==============================================================================

def bin_to_int(binary_str: str) -> int:
    """Converte string binária para inteiro, tratando o bit de sinal (complemento de dois)."""
    if not binary_str:
        return 0
    
    # Preenche para 32 bits (padrão do pipeline)
    while len(binary_str) < 32:
        binary_str = binary_str[0] + binary_str # Estende o bit de sinal

    # Verifica se é negativo (bit mais significativo é 1)
    if binary_str[0] == '1':
        # Converte para complemento de dois
        # 1. Inverte todos os bits
        inverted_bits = ''.join(['1' if b == '0' else '0' for b in binary_str])
        # 2. Soma 1 e inverte o sinal
        return -(int(inverted_bits, 2) + 1)
    else:
        return int(binary_str, 2)

def reg_to_bin(reg_str: str) -> str:
    """Converte nome de registrador (R0 a R15) para binário de 4 bits."""
    try:
        reg_num = int(reg_str[1:])
        if 0 <= reg_num <= 15:
            return format(reg_num, '04b')
        else:
            raise ValueError("Número do registrador fora do intervalo (0-15).")
    except (ValueError, IndexError):
        raise ValueError(f"Formato de registrador inválido: {reg_str}")

# ==============================================================================
# Definição e Decodificação das Instruções
# ==============================================================================

# --- DEFINIÇÃO COMPLETA DE INSTRUÇÕES (UFLA-RISC) ---
OPCODE_MAP = {
    # 1. Tipo R (0-12)
    '00000001': {'name': 'ADD', 'type': 'R'}, '00000010': {'name': 'SUB', 'type': 'R'},
    '00000011': {'name': 'ZERO', 'type': 'R'}, '00000100': {'name': 'XOR', 'type': 'R'},
    '00000101': {'name': 'OR', 'type': 'R'}, '00000110': {'name': 'NOT', 'type': 'R'},
    '00000111': {'name': 'AND', 'type': 'R'}, '00001000': {'name': 'SLA', 'type': 'R'},
    '00001001': {'name': 'SRA', 'type': 'R'}, '00001010': {'name': 'SLL', 'type': 'R'},
    '00001011': {'name': 'SRL', 'type': 'R'}, '00001100': {'name': 'COPY', 'type': 'R'},
    
    # NOVOS R-Type (20, 21, 27)
    '00010100': {'name': 'MUL', 'type': 'R'},  # 20
    '00010101': {'name': 'DIV', 'type': 'R'},  # 21
    '00011011': {'name': 'NOR', 'type': 'R'},  # 27

    # 2. Instruções Aritméticas Imediatas (I_ARITH) 
    # Opcodes Originais (24, 25)
    '00011000': {'name': 'ADDI', 'type': 'I_ARITH'}, # 24
    '00011001': {'name': 'SUBI', 'type': 'I_ARITH'}, # 25

    # NOVOS I-ARITH (22, 23, 28)
    '00010110': {'name': 'MULI', 'type': 'I_ARITH'}, # 22
    '00010111': {'name': 'ANDI', 'type': 'I_ARITH'}, # 23
    '00011100': {'name': 'SLTI', 'type': 'I_ARITH'}, # 28
    
    # 3. Instruções de Constante (I_CONST)
    '00001110': {'name': 'LUI', 'type': 'I_CONST'},   # 14
    '00011010': {'name': 'LLI', 'type': 'I_CONST'},   # 26

    # 4. Instruções de Memória (I_MEM)
    '00010000': {'name': 'LW', 'type': 'I_MEM'},# 16
    '00010001': {'name': 'SW', 'type': 'I_MEM'},# 17
    
    # 5. Controle
    '00000000': {'name': 'NOP', 'type': 'NOP'},
    '11111111': {'name': 'HALT', 'type': 'HALT'}
}

def decode_instruction(instruction_binary: str) -> dict:
    """Decodifica uma instrução binária de 32 bits, retornando seus campos."""
    
    opcode = instruction_binary[0:8]
    op_info = OPCODE_MAP.get(opcode)

    if not op_info:
        raise ValueError(f"Opcode não reconhecido: {opcode}")

    decoded = {'Opcode': opcode, 'Mnemonic': op_info['name'], 'Type': op_info['type']}

    if op_info['type'] in ['R', 'I_ARITH', 'I_MEM']:
        # Campos genéricos (R-Type: Rd/Rs/Rt, I-Type: Rt/Rs/Imm)
        F1 = instruction_binary[8:12]  # Rd (R) ou Rt (I)
        F2 = instruction_binary[12:16] # Rs
        F3 = instruction_binary[16:32] # Rt (R) ou Imm (I)

        decoded['Rs'] = int(F2, 2)
        
        if op_info['type'] == 'R':
            # Formato R: OP | Rd | Rs | Rt
            decoded['Rd'] = int(F1, 2)
            decoded['Rt'] = int(F3[0:4], 2)
        else: # I_ARITH, I_MEM
            # Formato I: OP | Rt | Rs | Imm
            decoded['Rt'] = int(F1, 2)
            # Immediato é um valor de 16 bits
            decoded['Immediate'] = bin_to_int(F3) 

    elif op_info['type'] == 'I_CONST':
        # Formato I_CONST: OP | Rt | Imm_H (8) | Imm_L (8)
        F1 = instruction_binary[8:12]  # Rt
        F2 = instruction_binary[12:20] # Imm_H
        F3 = instruction_binary[20:28] # Imm_L

        decoded['Rt'] = int(F1, 2)
        # O valor imediato completo é 16 bits, não assinado.
        imm_16_bin = F2 + F3
        decoded['Immediate'] = int(imm_16_bin, 2)

    return decoded