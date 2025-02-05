# /// script
# dependencies = ["prefect"]
# ///

"""
Demonstrates directly returning a state. In this case, we return a named Completed state
to indicate that a task SKIPPED execution in a way that is not an error.
"""

from prefect import task
from prefect.states import Completed


def get_work_to_do() -> list[str]:
    return []


@task(log_prints=True)
def main():
    work_to_do = get_work_to_do()

    if not work_to_do:
        return Completed(name="SKIPPED", message="No work to do")

    print(f"Proceeding to do work: {work_to_do}")


if __name__ == "__main__":
    main()
