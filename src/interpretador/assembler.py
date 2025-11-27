import os
import sys
# Importa o mapa de instruções para garantir consistência
from src.simulador.instruction import OPCODE_MAP

# --- CONTEÚDO PADRÃO DE ASSEMBLY ---
DEFAULT_ASSEMBLY_CONTENT = """
# Exemplo padrão de teste
ADDI R1, R0, 3  # R1 = 3 (I-ARITH)
MUL R2, R1, R1  # R2 = 9 (R-TYPE)
NOP             # Bolha 1
NOP             # Bolha 2
SW R2, 4(R0)    # Mem[4] = 9 (I-MEM)
LW R3, 4(R0)    # R3 = 9 (I-MEM)
HALT            # Fim
"""

# --- FUNÇÕES AUXILIARES DE CONVERSÃO ---

def reg_to_bin(reg_str: str) -> str:
    """
    Converte 'R1' para '0001' (4 bits). 
    *** CRITICAMENTE CORRIGIDO para 4 bits ***
    """
    try:
        index = int(reg_str[1:])
        if index < 0 or index > 15:
            raise ValueError()
        # Usa 4 bits para o registrador
        return format(index, '04b') 
    except:
        raise ValueError(f"Registrador inválido: {reg_str}")

def imm_to_bin(value: int, num_bits: int) -> str:
    """Converte valor inteiro (decimal) para binário de complemento de dois com 'num_bits'."""
    value = int(value)
    if value < 0: value = (1 << num_bits) + value
    # Trunca/expande para o número exato de bits
    return format(value, f'0{num_bits}b')

def assemble_line(assembly_line: str) -> str:
    """Converte uma linha de assembly para sua representação binária de 32 bits."""
    clean_line = assembly_line.strip() 
    # Ignora comentários e linhas vazias
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
        # Formato R: OP (8) | Rd (4) | Rs (4) | Rt (4) | Fill (12)
        Rd_bin = reg_to_bin(operands[0])
        Rs_bin = reg_to_bin(operands[1])
        
        # O F3 (os últimos 16 bits) é composto por Rt (4 bits) e 12 bits de preenchimento.
        # R-Type: OP(8) | F1(Rd, 4) | F2(Rs, 4) | F3 (Rt+Fill, 16)
        Rt_bin_4bits = reg_to_bin(operands[2]) if len(operands) == 3 else '0000'
        F3_bin = Rt_bin_4bits + '0' * 12 # 16 bits
        
        return op_bin + Rd_bin + Rs_bin + F3_bin

    elif op_info['type'] in ['I_ARITH', 'I_CONST', 'I_MEM']:
        
        # I-ARITH (ADDI, MULI, etc.)
        if op_info['type'] == 'I_ARITH':
            # Formato I_ARITH: OP (8) | Rt (4) | Rs (4) | Imm (16)
            Rt_bin = reg_to_bin(operands[0]) # Destino
            Rs_bin = reg_to_bin(operands[1]) # Fonte
            # CORREÇÃO CRÍTICA: O imediato deve ter 16 bits
            Imm_bin = imm_to_bin(int(operands[2]), 16) 
            return op_bin + Rt_bin + Rs_bin + Imm_bin
            
        # I-MEM (LW, SW)
        elif op_info['type'] == 'I_MEM':
            # Formato I_MEM: OP (8) | Rt (4) | Rs (4) | Offset (16)
            Rt_bin = reg_to_bin(operands[0])
            # Separa o offset do registrador base (ex: 4(R0) -> offset=4, Rs_str=R0)
            offset, Rs_str = operands[1].strip(')').split('(')
            Rs_bin = reg_to_bin(Rs_str)
            # CORREÇÃO CRÍTICA: O offset deve ter 16 bits
            Imm_bin = imm_to_bin(int(offset), 16) 
            return op_bin + Rt_bin + Rs_bin + Imm_bin
            
        # I-CONST (LUI, LLI, etc.)
        elif op_info['type'] == 'I_CONST':
            # Formato I_CONST: OP (8) | Rt (4) | Imm_H (8) | Imm_L (12)
            Rt_bin = reg_to_bin(operands[0])
            immediate_16_val = int(operands[1])
            # O imediato de 16 bits é dividido em Imm_H (8) e o restante (12)
            # Corrigindo para 16 bits completos: 8 para H e 8 para L
            imm_16_bin = format(immediate_16_val & 0xFFFF, '016b')
            Imm_H_bin = imm_16_bin[:8] # 8 bits
            Imm_L_bin = imm_16_bin[8:] # 8 bits
            
            # O seu decode espera I_CONST: OP(8) | Rt(4) | Imm_H(8) | Imm_L(12)
            # Revertendo o Imm_L para o que seu decode espera (12 bits)
            # Assumindo que o Imm_L deve ser preenchido com 4 zeros à direita para 12 bits
            
            # Formato original I_CONST (OP | F1 | F2 | F3): F1=Rt(4), F2=Imm_H(8), F3=Imm_L(12)
            # Onde Imm_L é tipicamente os 8 bits baixos + 4 zeros, resultando em 12 bits para F3
            # Se for esse o caso:
            
            # Vamos usar os 8 bits do Imm_L e adicionar 4 bits de fill para 12 bits (total de 20 bits de Imediato)
            Imm_L_12bits = imm_16_bin[8:] + '0' * 4 
            
            return op_bin + Rt_bin + Imm_H_bin + Imm_L_12bits
            
    return ""

# --- FUNÇÃO PRINCIPAL DE MONTAGEM ---

def assemble_file(input_file: str, output_file_txt: str, output_file_bin: str):
    """Lê o .asm e gera os arquivos .bin (bytes) e .txt (strings binárias)."""
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
                    # Verifica o tamanho da instrução
                    if binary_instruction and len(binary_instruction) == 32:
                        
                        outfile_txt.write(binary_instruction + '\n')
                        
                        # Converte a string binária para bytes (Big Endian)
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
    if not os.path.exists(asm_path) or os.stat(asm_path).st_size == 0:
        print(f"[ASSEMBLER] Criando arquivo de Assembly padrão: {asm_path}")
        with open(asm_path, 'w') as f:
            f.write(DEFAULT_ASSEMBLY_CONTENT.strip())
            
    # Sempre remontar se o bin não existir ou se for mais antigo que o asm
    should_assemble = not os.path.exists(bin_path)
    if os.path.exists(bin_path) and os.path.getmtime(asm_path) > os.path.getmtime(bin_path):
        should_assemble = True
        
    if should_assemble:
        print("\n--- 📝 FASE DE MONTAGEM AUTOMÁTICA ---")
        if not assemble_file(asm_path, txt_path, bin_path):
            # Não lança exceção, permite que o loader tente carregar o que puder
            return False 
        print("--- ✅ Montagem concluída. ---")
        return True
    return False

if __name__ == '__main__':
    # Teste de montagem (opcional)
    print("")