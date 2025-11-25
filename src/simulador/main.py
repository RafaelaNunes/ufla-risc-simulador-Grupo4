# main.py

import os
# Imports absolutos para o módulo
from src.simulador.cpu import CPU
from src.simulador.registers import create_registers
from src.simulador.memory import create_memory
from src.simulador.instruction import decode_instruction, OPCODE_MAP # Necessário para checar a decodificação

def load_program(file_path: str) -> tuple:
    """
    Lê o arquivo binário, carrega instruções na memória e determina o PC inicial.
    Retorna: (instruction_mem_dict, initial_pc)
    """
    instruction_mem_dict = {}
    current_pc = 0
    initial_pc = 0
    initial_pc_set = False

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de programa não encontrado: {file_path}")

    with open(file_path, 'r') as f:
        for line in f:
            raw_line = line.strip()
            if not raw_line: continue

            if raw_line.lower().startswith('address'):
                try:
                    address_str = raw_line.split()[1]
                    current_pc = int(address_str, 2)
                    if not initial_pc_set:
                        initial_pc = current_pc
                        initial_pc_set = True
                    print(f"[LOADER] PC base: 0x{current_pc:04X}")
                    continue
                except (IndexError, ValueError):
                    print(f"[LOADER] ERRO: Diretiva 'address' inválida.")
                    continue
            
            binary_string = raw_line
            if len(binary_string) == 32:
                instruction_mem_dict[current_pc] = binary_string
                current_pc += 4
            else:
                print(f"[LOADER] Aviso: Linha ignorada: {raw_line}")

    if not initial_pc_set:
         initial_pc = 0
         
    return instruction_mem_dict, initial_pc

def main():
    """Função principal para configurar e rodar a simulação da CPU."""
    program_file = 'binarios/teste.txt'
    

    try:
        # FASE 1: Carregamento do Programa
        instruction_mem_dict, initial_pc = load_program(program_file)
        
        if not instruction_mem_dict:
            print("Nenhuma instrução válida encontrada. Encerrando.")
            return

        # FASE 2: Inicialização do Hardware
        registers_list = create_registers()
        data_memory_list = create_memory()

        # FASE 3: Instanciação e Execução
        print("-" * 50)
        print(f"Simulação UFLA-RISC iniciada em PC: 0x{initial_pc:04X}")
        print("-" * 50)
        
        cpu = CPU(instruction_mem_dict, registers_list, initial_pc)
        cpu.run()
        
    except FileNotFoundError as e:
        print(f"ERRO FATAL: {e}")
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante a execução: {e}")

if __name__ == '__main__':
    if not os.path.isdir('binarios'):
        os.makedirs('binarios')
    
    main()