import pyrtl


def datapath(zero, lt, opcode):
    # opcode:
    # 00 = blt  -> branch when lt = 1
    # 01 = bge  -> branch when lt = 0
    # 10 = beq  -> branch when zero = 1
    # 11 = bne  -> branch when zero = 0

    relational = pyrtl.mux(opcode[0], lt, ~lt)
    equality = pyrtl.mux(opcode[0], zero, ~zero)

    branch = pyrtl.mux(opcode[1], relational, equality)

    return branch


if __name__ == "__main__":
    zero = pyrtl.Input(1, "zero")
    lt = pyrtl.Input(1, "lt")
    opcode = pyrtl.Input(2, "opcode")

    branch_out = datapath(zero, lt, opcode)

    branch = pyrtl.Output(1, "branch")
    branch <<= branch_out

    sim = pyrtl.Simulation()

    # Example test: blt, lt = 1 -> branch = 1
    sim.step({"zero": 0, "lt": 1, "opcode": 0})
    assert sim.inspect("branch") == 1

    # blt, lt = 0 -> branch = 0
    sim.step({"zero": 0, "lt": 0, "opcode": 0})
    assert sim.inspect("branch") == 0

    # bge, lt = 0 -> branch = 1
    sim.step({"zero": 0, "lt": 0, "opcode": 1})
    assert sim.inspect("branch") == 1

    # bge, lt = 1 -> branch = 0
    sim.step({"zero": 0, "lt": 1, "opcode": 1})
    assert sim.inspect("branch") == 0

    # beq, zero = 1 -> branch = 1
    sim.step({"zero": 1, "lt": 0, "opcode": 2})
    assert sim.inspect("branch") == 1

    # beq, zero = 0 -> branch = 0
    sim.step({"zero": 0, "lt": 0, "opcode": 2})
    assert sim.inspect("branch") == 0

    # bne, zero = 0 -> branch = 1
    sim.step({"zero": 0, "lt": 0, "opcode": 3})
    assert sim.inspect("branch") == 1

    # bne, zero = 1 -> branch = 0
    sim.step({"zero": 1, "lt": 0, "opcode": 3})
    assert sim.inspect("branch") == 0

    print("All tests passed!")