def simulation_scope(run_id: str) -> str:
    run_value = run_id.strip()
    if not run_value:
        raise ValueError("run_id is required")
    if run_value.startswith("sim-"):
        return run_value
    return f"sim-{run_value}"
