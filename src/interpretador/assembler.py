# src/interpretador/assembler.py

import os
import sys
# Importa o mapa de instruções para garantir consistência
from src.simulador.instruction import OPCODE_MAP, bin_to_int 

# --- CONTEÚDO PADRÃO DE ASSEMBLY ---
DEFAULT_ASSEMBLY_CONTENT = """

"""

# --- FUNÇÕES AUXILIARES DE CONVERSÃO ---
def reg_to_bin(reg_str: str) -> str:
    """Converte 'R1' para '00000001' (8 bits)"""
    if reg_str.upper() == 'R0': return '00000000'
    try:
        index = int(reg_str[1:])
        return format(index & 0xFF, '08b')
    except:
        raise ValueError(f"Registrador inválido: {reg_str}")

def imm_to_bin(value: int, num_bits: int = 8) -> str:
    """Converte valor inteiro (decimal) para binário de complemento de dois."""
    value = int(value)
    if value < 0: value = (1 << num_bits) + value
    return format(value, f'0{num_bits}b')

def assemble_line(assembly_line: str) -> str:
    """Converte uma linha de assembly para sua representação binária de 32 bits."""
    clean_line = assembly_line.strip() 
    if clean_line.startswith('#') or not clean_line: return ""
        
    parts = clean_line.replace(',', ' ').split()
    if not parts: return ""

    mnemonic = parts[0].upper()
    op_bin = next((op for op, info in OPCODE_MAP.items() if info['name'] == mnemonic), None)
    if not op_bin: raise ValueError(f"Mnemônico desconhecido: {mnemonic}")

    op_info = OPCODE_MAP[op_bin]
    operands = parts[1:]

    if op_info['type'] == 'HALT': return '11111111' + '0' * 24
    if op_info['type'] == 'NOP': return '0' * 32
        
    # Lógica de codificação R-Type, I-Type
    if op_info['type'] == 'R':
        # Formato: OP | Rd | Rs | Rt (COPY e NOT podem usar Rt como zero)
        Rd_bin = reg_to_bin(operands[0])
        Rs_bin = reg_to_bin(operands[1])
        Rt_bin = reg_to_bin(operands[2]) if len(operands) == 3 else '00000000'
        return op_bin + Rd_bin + Rs_bin + Rt_bin

    elif op_info['type'] in ['I_ARITH', 'I_CONST', 'I_MEM']:
        # Tipos I_ARITH e I_MEM (8-bit Imm)
        if op_info['type'] in ['I_ARITH']:
            # Formato: OP | Rd | Rs | Imm
            Rd_bin = reg_to_bin(operands[0])
            Rs_bin = reg_to_bin(operands[1])
            Imm_bin = imm_to_bin(int(operands[2]), 8)
            return op_bin + Rd_bin + Rs_bin + Imm_bin
            
        elif op_info['type'] == 'I_MEM':
            # Formato: OP | Rt | Rs | Imm (Offset)
            Rt_bin = reg_to_bin(operands[0])
            offset, Rs_str = operands[1].strip(')').split('(')
            Rs_bin = reg_to_bin(Rs_str)
            Imm_bin = imm_to_bin(int(offset), 8)
            return op_bin + Rt_bin + Rs_bin + Imm_bin
            
        elif op_info['type'] == 'I_CONST':
            # Formato: OP | Rt | Imm_H | Imm_L (16-bit Imm)
            Rt_bin = reg_to_bin(operands[0])
            immediate_16_val = int(operands[1])
            imm_16_bin = format(immediate_16_val & 0xFFFF, '016b')
            Imm_H_bin = imm_16_bin[:8]
            Imm_L_bin = imm_16_bin[8:]
            return op_bin + Rt_bin + Imm_H_bin + Imm_L_bin
        
    return ""

def assemble_file(input_file: str, output_file_txt: str, output_file_bin: str):
    """Lê o .asm e gera os arquivos .bin (bytes) e .txt (strings binárias)."""
    # ... (Função idêntica à do último passo para I/O) ...
    os.makedirs(os.path.dirname(output_file_txt), exist_ok=True)
    print(f"[ASSEMBLER] Montando {input_file} -> {os.path.basename(output_file_bin)}...")
    lines_written = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file_txt, 'w', encoding='utf-8') as outfile_txt, \
             open(output_file_bin, 'wb') as outfile_bin:
            
            outfile_txt.write("address 0000000000000000\n") 
            
            for line in infile:
                try:
                    binary_instruction = assemble_line(line)
                    if binary_instruction and len(binary_instruction) == 32:
                        
                        outfile_txt.write(binary_instruction + '\n')
                        
                        raw_bytes = bytes([
                            int(binary_instruction[0:8], 2), int(binary_instruction[8:16], 2), 
                            int(binary_instruction[16:24], 2), int(binary_instruction[24:32], 2) 
                        ])
                        outfile_bin.write(raw_bytes)
                        lines_written += 1
                except Exception as e:
                    print(f"[ASSEMBLER] ERRO na linha '{line.strip()}': {e}", file=sys.stderr)
            
    except Exception as e:
        print(f"[ASSEMBLER] ERRO FATAL de I/O: {e}", file=sys.stderr)
        return False

    if lines_written == 0:
        print("[ASSEMBLER] Aviso: Nenhuma instrução válida foi gerada.")
        return False
        
    print(f"[ASSEMBLER] Sucesso: {lines_written} instruções geradas.")
    return True

def check_and_generate_bin(asm_path: str, bin_path: str, txt_path: str):
    """Função chamada pelo main.py para garantir a existência do .bin."""
    
    os.makedirs(os.path.dirname(asm_path), exist_ok=True)
    if not os.path.exists(asm_path):
        print(f"[ASSEMBLER] Criando arquivo de Assembly padrão: {asm_path}")
        with open(asm_path, 'w') as f:
            f.write(DEFAULT_ASSEMBLY_CONTENT.strip())
            
    if not os.path.exists(bin_path):
        print("\n--- 📝 FASE DE MONTAGEM AUTOMÁTICA ---")
        if not assemble_file(asm_path, txt_path, bin_path):
            raise Exception("Falha ao gerar o arquivo binário.")
        print("--- ✅ Montagem concluída. ---")
        return True
    return False