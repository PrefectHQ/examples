# ---
# title: Hello, world!
# description: Your first steps with Prefect – learn how to create a basic flow and understand core concepts.
# icon: play
# dependencies: ["prefect"]
# cmd: ["python", "01_getting_started/01_hello_world.py"]
# tags: [getting_started, basics]
# draft: false
# ---
#
# Welcome to your first Prefect flow. In under a minute you will:
# 1. Ship production-ready orchestration code with **zero boilerplate**.
# 2. See live, structured logs without writing any logging boilerplate.
# 3. Understand how the very same Python stays portable from a laptop to Kubernetes (or Prefect Cloud).
#
# *Pro tip*: change anything in this file and re-run it. Prefect hot-loads your new logic in seconds, no image builds, ever.
#
# ## Importing Prefect and setting up

# We start by importing the essential `flow` decorator from Prefect.

from prefect import flow, tags

# ## Defining a flow

# Prefect takes your Python functions and transforms them into flows with enhanced capabilities.
#
# Let's write a simple function that takes a name parameter and prints a greeting.
#
# To make this function work with Prefect, we just wrap it in the `@flow` decorator.


@flow(log_prints=True)
def hello(name: str = "Marvin") -> None:
    """Log a friendly greeting."""
    print(f"Hello, {name}!")


# ## Running our flow locally and with parameters

# Now let's see different ways we can call that flow:
#
# 1. As a regular call with default parameters
# 2. With custom parameters
# 3. Multiple times to greet different people

if __name__ == "__main__":
    # run the flow with default parameters
    with tags(
        "test"
    ):  # This is a tag that we can use to filter the flow runs in the UI
        hello()  # Logs: "Hello, Marvin!"

        # run the flow with a different input
        hello("Marvin")  # Logs: "Hello, Marvin!"

        # run the flow multiple times for different people
        crew = ["Zaphod", "Trillian", "Ford"]

        for name in crew:
            hello(name)

# ## What just happened?

# When we decorated our function with `@flow`, the function was transformed into a Prefect flow. Each time we called it:
#
# 1. Prefect registered the execution as a flow run
# 2. It tracked all inputs, outputs, and logs
# 3. It maintained detailed state information about the execution
# 4. Added tags to the flow run to make it easier to find when observing the flow runs in the UI
#
# In short, we took a regular function and enhanced it with observability and tracking capabilities.

# ## But why does this matter?

# This simple example demonstrates Prefect's core value proposition: taking regular Python code and enhancing it with production-grade orchestration capabilities. Let's explore why this matters for real-world data workflows.


# ### You can change the code and run it again

# For instance, change the greeting message in the `hello` function to a different message and run the flow again.
# You'll see your changes immediately reflected in the logs.

# ### You can process more data

# Add more names to the `crew` list or create a larger data set to process. Prefect will handle each execution and track every input and output.

# ### You can run a more complex flow

# The `hello` function is a simple example, but in its place imagine something that matters to you, like:
#
# * ETL processes that extract, transform, and load data
# * Machine learning training and inference pipelines
# * API integrations and data synchronization jobs
#
# Prefect lets you orchestrate these operations effortlessly with automatic observability, error handling, and retries.

# ### Key Takeaways

# Remember that Prefect makes it easy to:
#
# * Transform regular Python functions into production-ready workflows with just a [decorator](https://docs.prefect.io/v3/develop/write-flows#write-and-run-flows)
# * Get automatic logging, [retries](https://docs.prefect.io/v3/develop/write-tasks#retries), and observability without extra code
# * Run the same code anywhere - from your laptop to production
# * Build complex data pipelines while maintaining simplicity
# * Track every execution with [detailed logs](https://docs.prefect.io/v3/develop/logging#configure-logging) and state information

# The `@flow` decorator is your gateway to enterprise-grade orchestration - no complex configuration needed!
#
#
# For more information about the orchestration concepts demonstrated in this example, see the [Prefect documentation](https://docs.prefect.io/).
