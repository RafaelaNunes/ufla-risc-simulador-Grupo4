
import os
import sys

from src.interpretador.assembler import check_and_generate_bin
from src.simulador.cpu import CPU, DataMemory, RegisterFile

def create_registers(): return [0] * 32
def create_data_memory(size_words=1024): return [0] * size_words

def load_program_bin(file_path_bin: str) -> tuple:
    instruction_mem_dict = {}
    if not os.path.exists(file_path_bin):
        raise FileNotFoundError(f"Arquivo .bin não encontrado: {file_path_bin}")

    try:
        with open(file_path_bin, 'rb') as f:
            current_pc = 0
            while True:
                instruction_bytes = f.read(4)
                if not instruction_bytes or len(instruction_bytes) != 4: break
                instruction_bin_str = ''.join(f'{b:08b}' for b in instruction_bytes)
                instruction_mem_dict[current_pc] = instruction_bin_str
                current_pc += 4
    except Exception as e:
        print(f"[LOADER] Erro: {e}", file=sys.stderr)
        raise
    return instruction_mem_dict, 0

def listar_e_escolher_arquivo(pasta_exemplos='exemplos'):
    if not os.path.exists(pasta_exemplos):
        print(f"Pasta '{pasta_exemplos}' não encontrada.")
        return None

    arquivos = [f for f in os.listdir(pasta_exemplos) if f.endswith('.asm')]
    arquivos.sort()

    if not arquivos:
        print("Nenhum arquivo .asm encontrado na pasta exemplos.")
        return None

    print("\n=== 📂 MENU DE SELEÇÃO DE TESTES ===")
    for i, arq in enumerate(arquivos):
        print(f"[{i+1}] {arq}")
    print("====================================")

    while True:
        try:
            escolha = input(f"Escolha o número do teste (1-{len(arquivos)}): ")
            idx = int(escolha) - 1
            if 0 <= idx < len(arquivos):
                return os.path.join(pasta_exemplos, arquivos[idx])
            else:
                print("Número inválido.")
        except ValueError:
            print("Entrada inválida. Digite um número.")

def main():
    if len(sys.argv) > 1:
        ASSEMBLY_SOURCE = sys.argv[1]
    else:
        selecionado = listar_e_escolher_arquivo()
        if not selecionado:
            return
        ASSEMBLY_SOURCE = selecionado

    if not os.path.exists(ASSEMBLY_SOURCE):
        print(f"ERRO: Arquivo não encontrado: {ASSEMBLY_SOURCE}")
        return

    base_name = os.path.basename(ASSEMBLY_SOURCE).replace('.asm', '')
    BINARY_OUTPUT_BIN = os.path.join('binarios', f'{base_name}.bin')
    BINARY_OUTPUT_TXT = os.path.join('binarios', f'{base_name}.txt')
    
    print(f"\n🚀 Iniciando Simulador para: {ASSEMBLY_SOURCE}")

    try:
        success = check_and_generate_bin(ASSEMBLY_SOURCE, BINARY_OUTPUT_BIN, BINARY_OUTPUT_TXT)
        if not success and not os.path.exists(BINARY_OUTPUT_BIN):
             print("Falha na montagem.")
             return
    except Exception as e:
        print(f"\nERRO FATAL NA MONTAGEM: {e}")
        return
        
    try:
        instruction_mem_dict, _ = load_program_bin(BINARY_OUTPUT_BIN)
        
        if not instruction_mem_dict:
            print("Nenhuma instrução carregada.")
            return

        registers_list = create_registers()
        data_memory_list = create_data_memory() 

        cpu = CPU(instruction_mem_dict, registers_list, data_memory_list)
        cpu.run()
        
    except Exception as e:
        print(f"Erro de execução: {e}")

if __name__ == '__main__':
    for p in ['binarios', 'exemplos', 'src/simulador', 'src/interpretador']:
        if not os.path.exists(p): os.makedirs(p, exist_ok=True)
        
    main()