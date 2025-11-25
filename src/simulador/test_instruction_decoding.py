# test_instruction_decoding.py

import os
# Importa a função de decodificação e o mapeamento de Opcodes
from src.simulador.instruction import decode_instruction, OPCODE_MAP 

def decode_pipeline_file(file_path):
    """
    Lê o arquivo de binário, decodifica cada linha e imprime o resultado, 
    lidando com a diretiva 'address' e a instrução 'HALT'.
    """
    print(f"--- 💻 Decodificação do UFLA-RISC a partir de {file_path} ---")
    
    if not os.path.exists(file_path):
        print(f"ERRO: Arquivo não encontrado no caminho: {file_path}")
        return

    current_pc = 0 
    
    try:
        with open(file_path, 'r') as f:
            for i, line in enumerate(f):
                raw_line = line.strip() 

                if not raw_line:
                    continue

                # 1. Checa a Diretiva 'address' (mantido)
                if raw_line.lower().startswith('address'):
                    try:
                        address_str = raw_line.split()[1]
                        current_pc = int(address_str, 2) 
                        print(f"\n[DIRETIVA] PC inicial definido para: 0x{current_pc:04X}")
                        continue
                    except (IndexError, ValueError):
                        print(f"\n[ERRO] Diretiva 'address' inválida na linha {i+1}.")
                        continue
                
                # 2. Processa a Instrução Binária
                binary_string = raw_line

                print(f"\n[Endereço 0x{current_pc:04X} | Linha {i+1}]")
                print(f"  Binário: {binary_string}")

                try:
                    # **MUDANÇA AQUI:** Chama a função de decodificação
                    inst_data = decode_instruction(binary_string)
                    
                    # Gera uma representação simplificada para o teste:
                    mnemonic = inst_data['mnemonic']
                    inst_type = inst_data['type']
                    
                    print(f"  Tipo: {inst_type} ({mnemonic})")
                    print(f"  Campos Decodificados: {inst_data}")

                    # 3. Condição de Parada HALT
                    if inst_type == 'HALT':
                        print("\n*** HALT DETECTADO. Processamento do pipeline encerrado. ***")
                        return 
                        
                except ValueError as e:
                    print(f"  ERRO de Formato: {e}")
                except Exception as e:
                    print(f"  ERRO de Decodificação: {e}")

                # 4. Atualiza o PC
                current_pc += 4 

    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")

if __name__ == '__main__':
    # Você pode manter este arquivo como um teste independente da CPU principal
    input_file = 'binarios/teste.txt'
    # Garante que o diretório exista antes de rodar.
    if not os.path.isdir('binarios'):
         os.makedirs('binarios')
    decode_pipeline_file(input_file)