# ---
# title: Transactions in Prefect
# description: Learn how to use Prefect's transaction system to ensure atomicity and handle rollbacks for your workflows.
# dependencies: ["prefect"]
# cmd: ["python", "04_misc/08_transactions.py"]
# tags: [transactions, resilience, atomicity]
# ---

# ## Transactions: Ensuring Atomicity in Your Workflows
#
# [Prefect Transactions](https://docs.prefect.io/v3/develop/transactions) allow you to treat
# multiple tasks as a single atomic unit. This means:
#
# * If any task in the transaction fails, the entire group is considered failed
# * Tasks can define **rollback** behavior to undo their effects when failures occur
# * Side effects can be automatically cleaned up if later tasks fail
# * Complex workflows can maintain data consistency even during failures
#
# ### Why Transactions Matter
#
# In data pipelines, tasks often create side effects (writing files, inserting database
# records, etc.). Without transactions, when a downstream task fails, you'd be left with
# partially completed work that might need manual cleanup.
#
# With Prefect transactions, you can:
#
# * **Define cleanup logic**: Write code that executes only when a transaction fails
# * **Ensure consistency**: Either all tasks in a group succeed or none do
# * **Simplify error handling**: No need for complex try/except blocks
# * **Maintain idempotency**: Run workflows multiple times without duplicate effects
#
# For a complete overview, see the [transactions documentation](https://docs.prefect.io/v3/develop/transactions).
#
# ### The Example: Data Quality Gate
#
# In this example, we'll demonstrate a common workflow pattern:
#
# 1. Write data to a file (or database, API, etc.)
# 2. Run quality checks on the data
# 3. If the quality check fails, automatically clean up the written data
#
# This pattern ensures bad data never remains in your system.
#
# ### Running the example
#
# ```bash
# python 02_sdk_concepts/06_transactions.py
# ```
#
# Try running with both valid and invalid data to see transactions in action.

import os
from time import sleep

from prefect import task, flow
from prefect.transactions import transaction


# ## Define tasks with rollback behavior
#
# First, we define a task that creates a side effect (writing to a file).
# We also attach an `on_rollback` handler that will be called if the
# transaction fails, ensuring cleanup. Learn more about [rollback hooks here](https://docs.prefect.io/v3/develop/transactions#write-your-first-transaction).


@task
def write_file(contents: str):
    """Writes data to a file.

    This task creates a side effect by writing to the filesystem,
    which will need to be cleaned up if the transaction fails.
    """
    with open("side-effect.txt", "w") as f:
        f.write(contents)


@write_file.on_rollback
def del_file(txn):
    """Delete the file when transaction fails.

    This function executes automatically if any task within the
    same transaction fails - even if the write_file task itself
    succeeded.
    """
    print("🧹 Cleaning up: Deleting the file")
    if os.path.exists("side-effect.txt"):
        os.unlink("side-effect.txt")


# Next, define a task that performs quality validation.
# This task will intentionally fail if the data doesn't meet
# our quality criteria.


@task
def quality_test():
    """Checks contents of file.

    This task enforces a data quality rule: the file must contain
    at least 2 lines of data. If not, it raises an error, which
    will trigger rollback of the entire transaction.
    """
    with open("side-effect.txt", "r") as f:
        data = f.readlines()

    if len(data) < 2:
        raise ValueError(
            "❌ Quality check failed: Not enough data! Need at least 2 lines."
        )

    print("✅ Quality check passed: Data meets requirements")


# ## The workflow with transaction
#
# Now we define our flow, which wraps both tasks in a single transaction.
# If quality_test fails, write_file's on_rollback handler will execute.


@flow(log_prints=True)
def pipeline(contents: str):
    """Process data with transaction-based cleanup.

    This flow demonstrates how to use transactions to ensure
    data consistency. If the quality check fails, the transaction
    rolls back and the file is deleted.

    Args:
        contents: The data to write to the file
    """
    print(f"🚀 Starting workflow with data: {contents}")

    # Create a transaction that groups our tasks
    with transaction() as txn:
        # Write data to file
        write_file(contents)

        # Brief pause so you can see the file appear
        print("📝 File created. Waiting 2 seconds before quality check...")
        sleep(2)

        # Run quality check - will fail if data has < 2 lines
        quality_test()

    print("✨ Transaction completed successfully")


# ## Execute the flow
#
# This example demonstrates both success and failure scenarios.

if __name__ == "__main__":
    # First run: This will fail the quality check (only one line)
    # and trigger the rollback, which deletes the file
    print("\n=== EXAMPLE 1: TRANSACTION THAT FAILS ===")
    try:
        pipeline(contents="single line of data")
    except Exception as e:
        print(f"💥 Expected error: {e}")

    # Second run: This will pass the quality check (two lines)
    # and the transaction will commit successfully
    print("\n=== EXAMPLE 2: TRANSACTION THAT SUCCEEDS ===")
    pipeline(contents="first line of data\nsecond line of data")


# ### What just happened?
#
# When you ran this script:
#
# 1. In the first run, the pipeline:
#    - Created a file with a single line of text
#    - Attempted to validate the data quality
#    - Failed the validation check (< 2 lines)
#    - **Automatically triggered the rollback**
#    - Deleted the file, leaving no trace of the failed operation
#
# 2. In the second run, the pipeline:
#    - Created a file with two lines of text
#    - Successfully validated the data quality
#    - Committed the transaction
#    - Left the file intact
#
# These benefits align with traditional database transaction principles, applied to workflow orchestration.
#
# ### Why This Is Important
#
# Transactions are critical for maintaining data integrity in production systems:
#
# * **Atomicity**: Either all steps succeed or none do - no partial effects
# * **Data Consistency**: Invalid data never persists in your systems
# * **Simplified Error Handling**: Declarative cleanup via on_rollback
# * **Reduced Manual Intervention**: No need to manually clean up after failures
#
# Transactions are especially valuable when working with multiple data stores
# that need to remain in sync, like when updating a database and a search index
# together, or when creating resources that have dependencies on each other.
#
# ### Advanced transaction features
#
# Prefect transactions can also:
#
# * **Share data**: [Store and retrieve values](https://docs.prefect.io/v3/develop/transactions#access-data-within-transactions) within the transaction context
# * **Ensure idempotency**: By using the [`key` parameter](https://docs.prefect.io/v3/develop/transactions#idempotency) to prevent duplicate runs
# * **Handle race conditions**: Execute safely in concurrent environments
# * **Support nested transactions**: Compose complex transaction hierarchies
#
# For more advanced use cases, see the [complete documentation on transactions](https://docs.prefect.io/v3/develop/transactions).
