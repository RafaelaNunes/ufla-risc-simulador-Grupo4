from src.simulador.memory import create_memory
from src.simulador.loader import load_binary_file
from src.simulador.cpu import CPU

def main():
    # 1. Cria memória e carrega o arquivo
    memory = create_memory()
    load_binary_file("binarios/teste_cpu.txt", memory)

    # 2. Cria CPU
    cpu = CPU(memory)

    # Inicializa valores de teste nos registradores
    cpu.registers[1] = 10
    cpu.registers[2] = 3

    print("Registradores iniciais:")
    print(cpu.registers)

    print("\n=== Iniciando execução ===")

    # 3. Executa passo a passo
    ciclo = 0
    while not cpu.halted:
        print(f"\n--- CICLO {ciclo} ---")
        print("PC antes:", cpu.pc)

        cpu.step()

        print("IR:", format(cpu.ir, "032b"))
        print("Opcode:", cpu.opcode)
        print("Registradores:", cpu.registers)
        print("Flags: N={}, Z={}, C={}, V={}".format(
            cpu.flag_neg, cpu.flag_zero, cpu.flag_carry, cpu.flag_overflow
        ))

        ciclo += 1
        if ciclo > 20:
            break

    print("\n=== Execução finalizada (HALT) ===")
    print("Registradores finais:")
    print(cpu.registers)

if __name__ == "__main__":
    main()
