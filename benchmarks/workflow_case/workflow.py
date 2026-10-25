
def resolve_workflow(
    dependencies: dict[str, list[str]]
) -> list[str]:
    """
    Return tasks in valid dependency order.

    Requirements:
    - Dependencies must execute before dependent tasks.
    - Shared dependencies are allowed.
    - Circular dependencies must raise ValueError.
    - Unknown dependencies must raise ValueError.
    - Ordering should be deterministic.
    """

    order = []
    visited = set()
    active = set()

    def visit(task: str) -> None:
        if task in active:
            raise ValueError("Dependency cycle")

        if task in visited:
            return

        if task not in dependencies:
            raise ValueError(f"Unknown task: {task}")

        active.add(task)

        for prerequisite in sorted(dependencies[task]):

            if prerequisite in visited:
                raise ValueError("Dependency cycle")

            visit(prerequisite)

        active.remove(task)
        visited.add(task)
        order.append(task)

    for task in sorted(dependencies):
        if task not in visited:
            visit(task)

    return order
