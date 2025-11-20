# src/simulador/main_loader.py

from src.simulador.memory import create_memory
from src.simulador.loader import load_binary_file, dump_loaded_memory
from src.simulador.cpu import CPU
import sys


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m src.simulador.main_loader binarios/arquivo.txt")
        return

    path = sys.argv[1]

    # Cria memória
    memory = create_memory()

    # Carregar binário
    try:
        next_addr = load_binary_file(path, memory, default_start=0)
    except Exception as e:
        print("Erro ao carregar arquivo:", e)
        return

    print(f"\nArquivo carregado com sucesso. Próximo endereço livre: {next_addr}\n")

    # Criar a CPU
    cpu = CPU(memory)

    print("=== Iniciando execução ===\n")

    # Executar até HALT
    while not cpu.halted:
        cpu.step()

    # Exibir resultado final
    print("\n=== Execução finalizada (HALT) ===")
    print("Registradores finais:")
    print(cpu.registers)

    print("\nDump de memória (posições não nulas):")
    dump_loaded_memory(memory, 0, 128)


if __name__ == "__main__":
    main()
