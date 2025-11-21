# src/simulador/test_cpu_pipeline.py
from src.simulador.memory import create_memory
from src.simulador.loader import load_binary_file
from src.simulador.cpu import CPU

def show_stage(name, reg):
    if not reg or not reg.get("valid", False):
        print(f"{name}: --- bolha ---")
        return
    ir = reg.get("ir", 0)
    opcode = reg.get("opcode", 0)
    print(f"{name}: IR={ir:032b} OPCODE={opcode}")

def main():
    mem = create_memory()
    load_binary_file("binarios/teste_pipeline.txt", mem)

    cpu = CPU(mem)
    # initialize registers for test
    from src.simulador.registers import write_reg
    write_reg(cpu.registers, 1, 100)  # base r1
    write_reg(cpu.registers, 3, 50)   # value r3
    # also preset mem[102] to read by LW (r1 + 2)
    mem[102] = 777

    print("Registradores iniciais:", cpu.registers[:8])
    ciclo = 0
    # run until halted and pipeline empty
    while not cpu.halted or cpu.any_pipeline_active():
        print(f"\n================ CICLO {ciclo} ================")
        print("\n--- antes ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        cpu.step()

        print("\n--- depois ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        print("\nRegistradores:", cpu.registers[:8])
        ciclo += 1
        if ciclo > 50:
            print("Interrompido (safety).")
            break

    print("\n=== FINAL ===")
    print("Registradores finais:", cpu.registers[:8])
    print("Mem[102] =", mem[102])
    print("Mem[104] =", mem[104])

if __name__ == "__main__":
    main()
