# src/simulador/main.py

import os
import sys
# Importa o Montador
from src.interpretador.assembler import check_and_generate_bin 
# Importa a CPU e as funções auxiliares
from src.simulador.cpu import CPU 
from src.simulador.registers import read_reg, write_reg
from src.simulador.memory import read_mem, write_mem

# --- MOCKS/AUXILIARES ---
def create_registers(): return [0] * 32 
def create_data_memory(size_words=1024): return [0] * size_words 
# -------------------------

def load_program_bin(file_path_bin: str) -> tuple:
    """Lê o arquivo .bin gerado e o carrega para a memória de instruções da CPU."""
    instruction_mem_dict = {}
    current_pc = 0
    initial_pc = 0 
    
    if not os.path.exists(file_path_bin):
        raise FileNotFoundError(f"ERRO FATAL: Arquivo .bin não encontrado.")

    print(f"[LOADER] Carregando instruções do arquivo: {os.path.basename(file_path_bin)}")

    try:
        with open(file_path_bin, 'rb') as f:
            while True:
                instruction_bytes = f.read(4) 
                if not instruction_bytes: break 
                if len(instruction_bytes) != 4: break
                
                instruction_bin_str = ''.join(f'{b:08b}' for b in instruction_bytes)
                instruction_mem_dict[current_pc] = instruction_bin_str
                current_pc += 4 
                
    except Exception as e:
        print(f"[LOADER] ERRO ao ler arquivo binário: {e}", file=sys.stderr)
        raise

    print(f"[LOADER] {len(instruction_mem_dict)} instruções carregadas.")
    return instruction_mem_dict, initial_pc


def main():
    
    ASSEMBLY_SOURCE = 'exemplos/teste_jump_to_branch.asm'
    base_name = os.path.basename(ASSEMBLY_SOURCE).replace('.asm', '')
    BINARY_OUTPUT_BIN = os.path.join('binarios', f'{base_name}.bin')
    BINARY_OUTPUT_TXT = os.path.join('binarios', f'{base_name}.txt')
    
    print(f"\n--- Simulador UFLA-RISC para {ASSEMBLY_SOURCE} ---")

    # 1. PASSO: GARANTIR A MONTAGEM (.asm -> .bin)
    try:
        check_and_generate_bin(ASSEMBLY_SOURCE, BINARY_OUTPUT_BIN, BINARY_OUTPUT_TXT)
    except Exception as e:
        print(f"\nERRO FATAL NA MONTAGEM: {e}")
        return
        
    # 2. PASSO: CARREGAMENTO (Lê o .bin)
    try:
        instruction_mem_dict, initial_pc = load_program_bin(BINARY_OUTPUT_BIN)
        
        if not instruction_mem_dict:
            print("Nenhuma instrução carregada. Encerrando.")
            return

        # 3. PASSO: CRIAÇÃO DE AMBIENTE E EXECUÇÃO
        
        # LISTAS SEPARADAS PARA REGISTRADORES E MEMÓRIA DE DADOS (FIX CRÍTICO)
        registers_list = create_registers()
        data_memory_list = create_data_memory() 

        print("\n--- INÍCIO DA EXECUÇÃO DO PIPELINE ---")
        
        # Passa as duas listas separadamente
        cpu = CPU(instruction_mem_dict, registers_list, data_memory_list)
        
        cpu.run() # Executa o pipeline e exibe o estado final
        
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante a execução: {e}")


if __name__ == '__main__':
    # Cria os diretórios necessários
    if not os.path.isdir('binarios'): os.makedirs('binarios')
    if not os.path.isdir('exemplos'): os.makedirs('exemplos')
    
    # Garante a estrutura de módulos
    if not os.path.isdir('src/simulador'): os.makedirs('src/simulador')
    if not os.path.isdir('src/interpretador'): os.makedirs('src/interpretador')
    
    main()