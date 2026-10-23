import pyrtl


if __name__ == "__main__":
    enable = pyrtl.Input(1, "enable")
    reset = pyrtl.Input(1, "reset")

    y = pyrtl.Register(2, "y")

    # Reset has priority.
    y.next <<= pyrtl.select(
        reset,
        0,
        pyrtl.select(enable, y + 1, y)
    )

    trace = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer=trace)

    # Reset
    sim.step({"reset": 1, "enable": 0})

    # Increment
    sim.step({"reset": 0, "enable": 1})
    sim.step({"reset": 0, "enable": 1})
    sim.step({"reset": 0, "enable": 1})

    # Hold
    sim.step({"reset": 0, "enable": 0})
    sim.step({"reset": 0, "enable": 0})

    # Reset has priority even when enable is also 1
    sim.step({"reset": 1, "enable": 1})

    # Increment again
    sim.step({"reset": 0, "enable": 1})
    sim.step({"reset": 0, "enable": 1})

    trace.render_trace()