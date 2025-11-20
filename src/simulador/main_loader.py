# src/simulador/main_loader.py

from src.simulador.memory import create_memory
from src.simulador.loader import load_binary_file, dump_loaded_memory
import sys


def main():
    if len(sys.argv) < 2:
        print("Uso: python main_loader.py binarios/exemplo_programa.txt")
        return

    path = sys.argv[1]
    mem = create_memory()
    try:
        next_addr = load_binary_file(path, mem, default_start=0)
    except Exception as e:
        print("Erro ao carregar arquivo:", e)
        return

    print(f"Arquivo carregado com sucesso. Proximo endereco livre: {next_addr}")
    dump_loaded_memory(mem, 0, 128)

if __name__ == "__main__":
    main()
