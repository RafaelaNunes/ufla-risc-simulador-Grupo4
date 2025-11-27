# src/simulador/instruction.py

# --- DEFINIÇÃO COMPLETA DE INSTRUÇÕES (UFLA-RISC) ---
OPCODE_MAP = {
    # 1. Tipo R (Formato: Op | Rd | Rs | Rt)
    '00000001': {'name': 'ADD', 'type': 'R'},   # Adição de inteiros
    '00000010': {'name': 'SUB', 'type': 'R'},   # Subtração de inteiros
    '00000011': {'name': 'ZERO', 'type': 'R'},  # Zero
    '00000100': {'name': 'XOR', 'type': 'R'},   # Xor
    '00000101': {'name': 'OR', 'type': 'R'},    # Or
    '00000110': {'name': 'NOT', 'type': 'R'},   # Not (Monadic: usa apenas Rs, Rd)
    '00000111': {'name': 'AND', 'type': 'R'},   # And
    '00001000': {'name': 'SLA', 'type': 'R'},   # Shift aritimético p/ esquerda
    '00001001': {'name': 'SRA', 'type': 'R'},   # Shift aritimético p/ direita
    '00001010': {'name': 'SLL', 'type': 'R'},   # Shift lógico à esquerda
    '00001011': {'name': 'SRL', 'type': 'R'},   # Shift lógico à direita
    '00001100': {'name': 'COPY', 'type': 'R'},  # Cópia (Monadic: R[Rd] <- R[Rs])

    # 2. Instruções Aritméticas Imediatas (Tipo I_ARITH: Op | Rd | Rs | Imm)
    '00011000': {'name': 'ADDI', 'type': 'I_ARITH'}, # Opcode 18
    '00011001': {'name': 'SUBI', 'type': 'I_ARITH'}, # Opcode 19
    
    # 3. Instruções de Constante (Tipo I_CONST: Op | Rt | Imm_H (8) | Imm_L (8))
    '00001110': {'name': 'LUI', 'type': 'I_CONST'}, # Carrega 16 bits nos 2 bytes MAIS sig.
    '00001111': {'name': 'LLI', 'type': 'I_CONST'}, # Carrega 16 bits nos 2 bytes MENOS sig.
    
    # 4. Instruções de Memória (Tipo I_MEM: Op | Rt | Rs | Imm (Offset))
    '00010000': {'name': 'LW', 'type': 'I_MEM'},    # Load Word
    '00010001': {'name': 'SW', 'type': 'I_MEM'},    # Store Word
    
    # 5. Controle
    '00000000': {'name': 'NOP', 'type': 'NOP'},  # NOP
    '11111111': {'name': 'HALT', 'type': 'HALT'} # Parada
}

def bin_to_int(binary_str: str) -> int:
    """Converte binário de 32 bits para inteiro assinado (complemento de dois)."""
    if not binary_str: return 0
    size = len(binary_str)
    # Verifica o bit de sinal
    if binary_str[0] == '1':
        # Valor negativo: complemento de dois
        return int(binary_str, 2) - (1 << size)
    return int(binary_str, 2)

def decode_instruction(instruction_binary: str) -> dict:
    """Decodifica uma instrução binária de 32 bits e retorna seus campos."""
    if len(instruction_binary) != 32:
        raise ValueError("Instrução binária inválida.")
        
    opcode_bin = instruction_binary[0:8]
    op_info = OPCODE_MAP.get(opcode_bin)
    
    if not op_info:
        return {'mnemonic': 'UNKNOWN', 'opcode_bin': opcode_bin}

    decoded = {'opcode_bin': opcode_bin, 'mnemonic': op_info['name'], 'type': op_info['type']}
    
    # Campos base: 8 bits cada
    F1 = instruction_binary[8:16]
    F2 = instruction_binary[16:24]
    F3 = instruction_binary[24:32]
    
    if op_info['type'] == 'R':
        # R-Type: F1=Rd, F2=Rs, F3=Rt
        decoded['Rd'] = int(F1, 2)
        decoded['Rs'] = int(F2, 2)
        decoded['Rt'] = int(F3, 2)
        
    elif op_info['type'] in ['I_ARITH', 'I_MEM']:
        # I-Type: F1=Rt/Rd, F2=Rs, F3=Imm (8 bits)
        decoded['Rt'] = int(F1, 2) 
        decoded['Rs'] = int(F2, 2)
        decoded['Immediate'] = bin_to_int(F3) # Imediato de 8 bits
        
    elif op_info['type'] == 'I_CONST':
        # I-CONST: F1=Rt, F2=Imm_H (8), F3=Imm_L (8)
        decoded['Rt'] = int(F1, 2)
        imm_16_bin = F2 + F3
        decoded['Immediate'] = bin_to_int(imm_16_bin)
        
    return decoded