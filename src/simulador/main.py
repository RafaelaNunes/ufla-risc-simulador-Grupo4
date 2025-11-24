# main.py

# Importa a lógica principal e os componentes de estado
from src.simulador.cpu import CPU
from src.simulador.registers import create_registers
from src.simulador.memory import create_memory

# Importa a lógica de decodificação para validação (opcional)
from instruction import Instruction 

import os

def load_program(file_path: str) -> tuple:
    """
    Lê o arquivo binário do UFLA-RISC, carrega as instruções na memória 
    e determina o PC inicial.
    
    Retorna: (instruction_mem_dict, initial_pc)
    """
    instruction_mem_dict = {}
    current_pc = 0
    initial_pc_set = False

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo de programa não encontrado: {file_path}")

    with open(file_path, 'r') as f:
        for line in f:
            raw_line = line.strip()
            if not raw_line:
                continue

            # 1. Processa a Diretiva 'address'
            if raw_line.lower().startswith('address'):
                try:
                    address_str = raw_line.split()[1]
                    # Assume que o endereço é dado em binário (como no seu exemplo)
                    current_pc = int(address_str, 2)
                    if not initial_pc_set:
                        initial_pc = current_pc
                        initial_pc_set = True
                    print(f"[LOADER] Novo PC base definido para: 0x{current_pc:04X}")
                    continue
                except (IndexError, ValueError):
                    print(f"[LOADER] ERRO: Diretiva 'address' inválida na linha: {raw_line}")
                    continue
            
            # 2. Carrega a Instrução Binária
            binary_string = raw_line
            if len(binary_string) == 32:
                # Carrega o binário na memória de instruções
                instruction_mem_dict[current_pc] = binary_string
                # Incrementa o PC para a próxima instrução (endereçamento à palavra)
                current_pc += 4
            else:
                print(f"[LOADER] Aviso: Linha ignorada por não ter 32 bits: {raw_line}")

    # Garante que haja um PC inicial, mesmo que não haja diretiva 'address'
    if not initial_pc_set:
         initial_pc = 0
         
    return instruction_mem_dict, initial_pc

def main():
    """Função principal para configurar e rodar a simulação da CPU."""
    program_file = 'binarios/teste_pipeline.txt'
    
    try:
        # FASE 1: Carregamento do Programa
        instruction_mem_dict, initial_pc = load_program(program_file)
        
        if not instruction_mem_dict:
            print("Nenhuma instrução válida encontrada para simulação. Encerrando.")
            return

        # FASE 2: Inicialização do Hardware
        # O UFLA-RISC usa o mesmo array para registradores e memória de dados
        registers_list = create_registers()
        data_memory_list = create_memory()

        # FASE 3: Instanciação e Execução da CPU
        print("-" * 50)
        print(f"Iniciando Simulação UFLA-RISC em PC inicial: 0x{initial_pc:04X}")
        print(f"Total de Instruções Carregadas: {len(instruction_mem_dict)}")
        print("-" * 50)
        
        # A CPU usa o dicionário de instruções e as listas de registradores/memória
        cpu = CPU(instruction_mem_dict, registers_list, initial_pc)
        
        # Roda o simulador de pipeline (ciclo a ciclo)
        cpu.run()
        
    except FileNotFoundError as e:
        print(f"ERRO FATAL: {e}")
    except Exception as e:
        print(f"Um erro inesperado ocorreu durante a execução: {e}")

if __name__ == '__main__':
    # Garante que o diretório binarios exista
    if not os.path.isdir('binarios'):
        os.makedirs('binarios')
    
    # Executa a simulação
    main()