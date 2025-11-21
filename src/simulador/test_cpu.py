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
    # Adicionando uma inicialização para o valor que será lido pelo LW no endereco 12
    # Base R1=10, Offset=2 -> Endereco 12.
    mem[12] = 777 
    load_binary_file("binarios/teste_pipeline.txt", mem)

    cpu = CPU(mem)
    # initialize registers for test
    from src.simulador.registers import write_reg
    
    # Ajustando inicialização para refletir o trace (R1=10, R2=3)
    #write_reg(cpu.registers, 1, 10)  # base r1
    #write_reg(cpu.registers, 2, 3)   # value r2 (assumindo que o R3=0 no trace original era R2=3)

    print("Registradores iniciais:", cpu.registers[:8])
    ciclo = 0
    # run until halted and pipeline empty
    while not cpu.halted or cpu.any_pipeline_active():
        print(f"\n================ CICLO {ciclo} ================")
        print("\n--- Antes do clock ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        cpu.step()

        print("\n--- Depois do clock ---")
        show_stage("IF/ID", cpu.IF_ID)
        show_stage("ID/EX", cpu.ID_EX)
        show_stage("EX/MEM", cpu.EX_MEM)
        show_stage("MEM/WB", cpu.MEM_WB)

        print("\nRegistradores:", cpu.registers[:8])
        print(f"Flags: N={cpu.flag_neg}, Z={cpu.flag_zero}, C={cpu.flag_carry}, V={cpu.flag_overflow}")
        ciclo += 1
        if ciclo > 10: # Aumentando o limite para garantir que o pipeline esvazie
            print("Interrompido (safety).")
            break

    print("\n=== EXECUÇÃO FINALIZADA ===")
    print("Registradores finais:", cpu.registers[:8])
    print("Mem[12] =", mem[12])
    print("Mem[1000] =", mem[1000]) # Endereço de escrita do SW
    print(f"Flags finais: N={cpu.flag_neg}, Z={cpu.flag_zero}, C={cpu.flag_carry}, V={cpu.flag_overflow}")

if __name__ == "__main__":
    main()