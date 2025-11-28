# src/interpretador/assembler.py

import os
import sys
from src.simulador.instruction import OPCODE_MAP

DEFAULT_ASSEMBLY_CONTENT = """
# Teste UFLA-RISC (Sanidade)
# Este programa testa operacoes basicas e o formato de instrucao
ADDI R1, R0, 10
ADDI R2, R0, 20
ADD R3, R1, R2
SW R3, R0
HALT
"""

def reg_to_bin(reg_str: str, bits=8) -> str:
    """Converte 'RX' para binário de N bits."""
    try:
        # Remove caracteres indesejados caso venha "R1,"
        clean_str = reg_str.replace(',', '').replace('(', '').replace(')', '')
        idx = int(clean_str.upper().replace('R', ''))
        if idx < 0 or idx > 31: raise ValueError
        return format(idx, f'0{bits}b')
    except:
        raise ValueError(f"Registrador inválido: {reg_str}")

def imm_to_bin(val_str: str, bits: int) -> str:
    """Converte string numérica para binário de N bits (complemento de 2)."""
    try:
        val = int(val_str.replace(',', '').replace('(', '').replace(')', ''))
        if val < 0: val = (1 << bits) + val
        return format(val & ((1 << bits) - 1), f'0{bits}b')
    except:
        raise ValueError(f"Imediato inválido: {val_str}")

def assemble_line(line: str) -> str:
    """Traduz uma linha de assembly para 32 bits binários."""
    # Limpeza básica: remove comentários e espaços extras
    line = line.split('#')[0].strip()
    if not line: return ""

    # Normaliza separadores para facilitar o split
    parts = line.replace(',', ' ').replace('(', ' ').replace(')', ' ').split()
    if not parts: return ""
    
    mnem = parts[0].upper()
    
    # Busca o opcode pelo nome no mapa corrigido
    op_bin = next((k for k, v in OPCODE_MAP.items() if v['name'] == mnem), None)
    if not op_bin: 
        raise ValueError(f"Instrução desconhecida: {mnem}")
    
    info = OPCODE_MAP[op_bin]
    t = info['type']
    
    if mnem == 'HALT': return '1' * 32
    if mnem == 'NOP': return '0' * 32

    # --- LÓGICA DE MONTAGEM (Formatos do PDF) ---

    # R-Type Padrão: ADD Rc, Ra, Rb -> Bin: Op(8) | Ra(8) | Rb(8) | Rc(8)
    if t == 'R':
        if len(parts) < 4: raise ValueError(f"Faltam operandos para {mnem}")
        rc = reg_to_bin(parts[1], 8) # Destino (1º arg no assembly)
        ra = reg_to_bin(parts[2], 8) # Fonte 1
        rb = reg_to_bin(parts[3], 8) # Fonte 2
        return op_bin + ra + rb + rc

    # R-Type Especiais (NOT, COPY)
    if t == 'R_NOT' or t == 'R_COPY': 
        # COPY Rc, Ra -> Bin: Op | Ra | 0 | Rc
        if len(parts) < 3: raise ValueError(f"Faltam operandos para {mnem}")
        rc = reg_to_bin(parts[1], 8)
        ra = reg_to_bin(parts[2], 8)
        return op_bin + ra + ('0'*8) + rc
    
    if t == 'R_SPECIAL': # ZERO Rc -> Bin: Op | 0 | 0 | Rc
        rc = reg_to_bin(parts[1], 8)
        return op_bin + ('0'*16) + rc

    # Memória: LOAD Rc, Ra (Load Rc from Mem[Ra])
    if t == 'MEM': 
        if len(parts) < 3: raise ValueError(f"Faltam operandos para {mnem}")
        rc = reg_to_bin(parts[1], 8)
        ra = reg_to_bin(parts[2], 8)
        # PDF LOAD: Op | Ra | ... | Rc
        return op_bin + ra + ('0'*8) + rc

    # Memória Store: STORE Rc, Ra (Store Mem[Rc] = Ra)
    if t == 'MEM_S':
        if len(parts) < 3: raise ValueError(f"Faltam operandos para {mnem}")
        rc = reg_to_bin(parts[1], 8) # Endereço
        ra = reg_to_bin(parts[2], 8) # Valor
        # PDF STORE: Op | Ra | ... | Rc
        return op_bin + ra + ('0'*8) + rc

    # I-CONST (LCL): LUI Rc, Const16
    if t == 'LCL':
        rc = reg_to_bin(parts[1], 8)
        imm = imm_to_bin(parts[2], 16)
        # PDF: Op | Const16 | Rc
        return op_bin + imm + rc

    # CUSTOM (Suas instruções novas): ADDI Rt, Rs, Imm
    # Formato Híbrido: Op(8) | Rt(4) Rs(4) | Imm(16)
    if t == 'I_CUSTOM':
        rt = reg_to_bin(parts[1], 4)
        rs = reg_to_bin(parts[2], 4)
        imm = imm_to_bin(parts[3], 16)
        return op_bin + rt + rs + imm

    # BRANCH: BEQ Ra, Rb, End
    if t == 'BRANCH':
        ra = reg_to_bin(parts[1], 8)
        rb = reg_to_bin(parts[2], 8)
        imm = imm_to_bin(parts[3], 8) # Endereço curto no PDF
        return op_bin + ra + rb + imm

    # JUMPS
    if t == 'JUMP' or t == 'J_LINK': # J End / JAL End
        imm = imm_to_bin(parts[1], 24)
        return op_bin + imm

    if t == 'J_REG': # JR Rc
        rc = reg_to_bin(parts[1], 8)
        return op_bin + ('0'*16) + rc

    return '0'*32 # Fallback

def assemble_file(input_file: str, output_file_txt: str, output_file_bin: str):
    """Lê arquivo ASM, gera TXT (strings binárias) e BIN (bytes)."""
    os.makedirs(os.path.dirname(output_file_txt), exist_ok=True)
    lines_written = 0
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file_txt, 'w', encoding='utf-8') as outfile_txt, \
             open(output_file_bin, 'wb') as outfile_bin:

            # Diretiva address obrigatória no início (PDF Apêndice A)
            outfile_txt.write("address 0000000000000000\n")
            
            for line in infile:
                try:
                    binary_instruction = assemble_line(line)
                    if binary_instruction and len(binary_instruction) == 32:
                        outfile_txt.write(binary_instruction + '\n')
                        # Converte string binária para bytes reais
                        raw_bytes = bytes([
                            int(binary_instruction[0:8], 2),
                            int(binary_instruction[8:16], 2),
                            int(binary_instruction[16:24], 2),
                            int(binary_instruction[24:32], 2)
                        ])
                        outfile_bin.write(raw_bytes)
                        lines_written += 1
                except Exception as e:
                    print(f"[ASSEMBLER] Erro na linha '{line.strip()}': {e}", file=sys.stderr)
    except Exception as e:
        print(f"[ASSEMBLER] Erro de arquivo: {e}", file=sys.stderr)
        return False

    if lines_written == 0:
        print("[ASSEMBLER] Aviso: Nenhuma instrução válida gerada.")
        return False

    print(f"[ASSEMBLER] Sucesso: {lines_written} instruções montadas.")
    return True

def check_and_generate_bin(asm_path: str, bin_path: str, txt_path: str):
    """Verifica se precisa recompilar o ASM (se bin não existe ou asm é mais novo)."""
    os.makedirs(os.path.dirname(asm_path), exist_ok=True)
    
    # Cria exemplo default se não existir
    if not os.path.exists(asm_path) or os.stat(asm_path).st_size == 0:
        with open(asm_path, 'w') as f:
            f.write(DEFAULT_ASSEMBLY_CONTENT.strip())
    
    should_assemble = not os.path.exists(bin_path)
    if os.path.exists(bin_path) and os.path.getmtime(asm_path) > os.path.getmtime(bin_path):
        should_assemble = True
        
    if should_assemble:
        print("\n--- 📝 MONTAGEM AUTOMÁTICA ---")
        return assemble_file(asm_path, txt_path, bin_path)
    
    return True