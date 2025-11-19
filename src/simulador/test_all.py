import sys
from src.simulador.cpu import CPU
from src.simulador.memory import create_memory, MEMORY_SIZE_WORDS
from src.simulador.loader import load_binary_file

def run_test(file):
    print("\n======================================")
    print(f"🔥 Rodando teste: {file}")
    print("======================================")

    memory = create_memory()
    cpu = CPU(memory)

    # cria registradores iniciais para cada teste
    cpu.registers[1] = 10
    cpu.registers[2] = 20
    cpu.registers[3] = 3
    cpu.registers[4] = 4
    cpu.registers[5] = 5
    cpu.registers[6] = 6
    cpu.registers[7] = 7
    cpu.registers[8] = 8
    cpu.registers[9] = 9
    cpu.registers[10] = 10

    # carrega arquivo binário
    load_binary_file(file, memory)

    # executa
    cpu.run()

    print("\n--- Registradores finais ---")
    print(cpu.registers)

    print("\n--- Memória (primeiros 16 endereços) ---")
    print(memory[:16])

def main():
    tests = [
        "binarios/test_shifts.txt",
        "binarios/test_consts_ldst.txt",
        "binarios/test_jumps.txt"
    ]

    for t in tests:
        run_test(t)


if __name__ == "__main__":
    main()
