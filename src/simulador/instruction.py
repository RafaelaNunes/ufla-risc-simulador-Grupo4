
def bin_to_int(binary_str: str) -> int:
    if not binary_str: return 0
    if len(binary_str) < 32:
        sign = binary_str[0]
        binary_str = sign * (32 - len(binary_str)) + binary_str
    
    if binary_str[0] == '1':
        inverted = ''.join('1' if b == '0' else '0' for b in binary_str)
        return -(int(inverted, 2) + 1)
    else:
        return int(binary_str, 2)


OPCODE_MAP = {
    
    '00000001': {'name': 'ADD', 'type': 'R'},
    '00000010': {'name': 'SUB', 'type': 'R'},
    '00000011': {'name': 'ZERO', 'type': 'R_SPECIAL'},
    '00000100': {'name': 'XOR', 'type': 'R'},
    '00000101': {'name': 'OR', 'type': 'R'},
    '00000110': {'name': 'NOT', 'type': 'R_NOT'},
    '00000111': {'name': 'AND', 'type': 'R'},
    '00001000': {'name': 'SLA', 'type': 'R'},
    '00001001': {'name': 'SRA', 'type': 'R'},
    '00001010': {'name': 'SLL', 'type': 'R'},
    '00001011': {'name': 'SRL', 'type': 'R'},
    '00001100': {'name': 'COPY', 'type': 'R_COPY'},
    
    '00001110': {'name': 'LUI', 'type': 'LCL'},
    '00001111': {'name': 'LLI', 'type': 'LCL'},
    
    '00010000': {'name': 'LW', 'type': 'MEM'},
    '00010001': {'name': 'SW', 'type': 'MEM_S'},
    
    '00010010': {'name': 'JAL', 'type': 'J_LINK'},
    '00010011': {'name': 'JR', 'type': 'J_REG'},
    '00010100': {'name': 'BEQ', 'type': 'BRANCH'},
    '00010101': {'name': 'BNE', 'type': 'BRANCH'},
    '00010110': {'name': 'J', 'type': 'JUMP'},

    '00010111': {'name': 'MUL', 'type': 'R'},
    '00011000': {'name': 'DIV', 'type': 'R'},
    '00011001': {'name': 'NOR', 'type': 'R'},
    
    '00011010': {'name': 'ADDI', 'type': 'I_CUSTOM'},
    '00011011': {'name': 'SUBI', 'type': 'I_CUSTOM'},
    '00011100': {'name': 'MULI', 'type': 'I_CUSTOM'},
    '00011101': {'name': 'ANDI', 'type': 'I_CUSTOM'},
    '00011110': {'name': 'SLTI', 'type': 'I_CUSTOM'},

    '11111111': {'name': 'HALT', 'type': 'HALT'},
    '00000000': {'name': 'NOP', 'type': 'NOP'}
}


def decode_instruction(instruction_binary: str) -> dict:
    if not instruction_binary or len(instruction_binary) < 32:
        return {'Mnemonic': 'NOP', 'Opcode': '00000000'}

    opcode = instruction_binary[0:8]
    op_info = OPCODE_MAP.get(opcode, {'name': 'UNKNOWN', 'type': 'UNKNOWN'})
    t = op_info['type']
    
    decoded = {
        'Opcode': opcode,
        'Mnemonic': op_info['name'],
        'Rs': 0, 'Rt': 0, 'Rd': 0, 'Immediate': 0
    }

    ra = int(instruction_binary[8:16], 2)
    rb = int(instruction_binary[16:24], 2)
    rc = int(instruction_binary[24:32], 2)

    if t == 'R': 
        decoded['Rs'] = ra
        decoded['Rt'] = rb
        decoded['Rd'] = rc
        
    elif t == 'R_NOT' or t == 'R_COPY':
        decoded['Rs'] = ra
        decoded['Rd'] = rc
        
    elif t == 'R_SPECIAL': 
        decoded['Rd'] = rc
        
    elif t == 'LCL':
        decoded['Rd'] = rc
        decoded['Immediate'] = int(instruction_binary[8:24], 2)
        
    elif t == 'MEM':
        decoded['Rs'] = ra
        decoded['Rd'] = rc
        
    elif t == 'MEM_S':
        decoded['Rs'] = rc
        decoded['Rt'] = ra
        
    elif t == 'BRANCH':
        decoded['Rs'] = ra
        decoded['Rt'] = rb
        decoded['Immediate'] = rc
        
    elif t == 'I_CUSTOM':
        decoded['Rt'] = int(instruction_binary[8:12], 2)
        decoded['Rs'] = int(instruction_binary[12:16], 2)
        decoded['Immediate'] = bin_to_int(instruction_binary[16:32])
        
    elif t == 'JUMP' or t == 'J_LINK':
        decoded['Immediate'] = int(instruction_binary[8:32], 2)
        
    elif t == 'J_REG':
        decoded['Rs'] = rc

    return decoded