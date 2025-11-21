from src.simulador.memory import create_memory
from src.simulador.loader import load_binary_file
from src.simulador.cpu import CPU

def show_stage(name, reg):
    """Exibe um estágio do pipeline"""
    if not reg or reg.get("ir") is None:
        print(f"{name}: --- bolha ---")
        return

    ir = reg["ir"]
    opcode = reg.get("opcode", None)

    print(f"{name}: IR={ir:032b} OPCODE={opcode}")

def main():
    # 1. Cria memória e carrega instruções
    memory = create_memory()
    load_binary_file("binarios/teste_cpu.txt", memory)

    # 2. Instancia CPU pipelined
    cpu = CPU(memory)

    # 3. Inicializa registradores para teste
    cpu.registers[1] = 10
    cpu.registers[2] = 3

    print("Registradores iniciais:")
    print(cpu.registers)
    print("\n=== INICIANDO EXECUÇÃO PIPELINED ===\n")

    ciclo = 0

    while not cpu.halted:


        print(f"\n================ CICLO {ciclo} ================")

        # Mostrar estágios ANTES do ciclo
        print("\n--- Antes do clock ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        cpu.step()

        # Mostrar estágios DEPOIS do ciclo
        print("\n--- Depois do clock ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        print("\nRegistradores:", cpu.registers)
        print("Flags: N={}, Z={}, C={}, V={}".format(
            cpu.flag_neg, cpu.flag_zero, cpu.flag_carry, cpu.flag_overflow
        ))

        ciclo += 1
        if ciclo > 40:
            print("Interrompido para evitar loop infinito.")
            break

    print("\n=== EXECUÇÃO FINALIZADA ===")
    print("Registradores finais:")
    print(cpu.registers)

if __name__ == "__main__":
    main()
