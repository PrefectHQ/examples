# ---
# title: [Scenario Name] – [Short Catchy Description]
# description: Learn how to [accomplish specific task] with Prefect – [brief description of the solution].
# dependencies: ["prefect", "other_dependencies"]
# cmd: ["python", "[directory]/[filename].py"]
# tags: [relevant, tags, for, scenario]
# ---

# ## [Scenario Name] – [Short Catchy Description]
#
# [One paragraph introduction to the specific scenario/problem this example solves]
#
# This example demonstrates these Prefect features:
# * [`[Prefect Feature]`](https://docs.prefect.io/[feature-path]) – [Brief explanation of what it does and why we're using it in this scenario]
# * [`[Prefect Feature]`](https://docs.prefect.io/[feature-path]) – [Brief explanation of what it does and why we're using it in this scenario]
# * [`[Prefect Feature]`](https://docs.prefect.io/[feature-path]) – [Brief explanation of what it does and why we're using it in this scenario]
#
# ### The Scenario: [Specific Use Case]
# [1-2 paragraphs describing the specific problem or workflow being addressed. Include real-world context and pain points]
#
# ### Our Solution
# [1-2 paragraphs outlining the approach we're taking to solve this problem with Prefect]
#
# For more information about [relevant concept], see the [Prefect documentation on this topic](https://docs.prefect.io/[concept-path]).
#
# ### Running the example locally
# ```bash
# python [directory]/[filename].py
# ```
# [Brief explanation of what happens when you run the example]
#
# ## Code walkthrough
# 1. **Imports & setup** – [Brief explanation of imports and setup]
# 2. **[Component 1]** – [Brief explanation of first major code component]
# 3. **[Component 2]** – [Brief explanation of second major code component]
# 4. **[Component 3]** – [Brief explanation of third major code component]
# 5. **Execution** – [Brief explanation of how the code runs]

from prefect import flow, task

# ---------------------------------------------------------------------------
# [Component 1 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [Brief explanation of this component, highlight any Prefect features being used]
# [For more details, see [documentation link](https://docs.prefect.io/[relevant-path])]


def example_function():
    """Docstring explaining function purpose."""
    # Implementation
    pass


# ---------------------------------------------------------------------------
# [Component 2 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [Brief explanation of this component, highlight any Prefect features being used]
# [Learn more about tasks in the [Prefect documentation](https://docs.prefect.io/concepts/tasks)]


@task(retries=2, retry_delay_seconds=5)
def example_task():
    """Docstring explaining task purpose."""
    # Implementation
    pass


# ---------------------------------------------------------------------------
# [Component 3 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [Brief explanation of this component, highlight any Prefect features being used]
# [Learn more about flows in the [Prefect documentation](https://docs.prefect.io/concepts/flows)]


@flow(log_prints=True)
def example_flow(param1="default_value"):
    """
    [Flow docstring with clear explanation of this flow's role in the scenario]
    """
    # Flow implementation
    pass


# ### What Just Happened?
# [Step-by-step explanation of what happened when the code ran, specifically highlighting Prefect features in action]
#
# Here's the sequence of events:
# 1. [First step in the execution with focus on Prefect features]
# 2. [Second step in the execution with focus on Prefect features]
# 3. [Third step in the execution with focus on Prefect features]
# 4. [Fourth step in the execution with focus on Prefect features]
#
# **[Key insight about how Prefect helped solve this scenario]** [Brief explanation of why this matters]
#
# For more information about the orchestration concepts demonstrated in this example, see the [Prefect documentation](https://docs.prefect.io/[relevant-path]).
#
# ### Why This Matters
#
# [1-2 paragraphs explaining how this Prefect-powered solution addresses the specific scenario. Focus on practical benefits like reliability, observability, maintainability, etc.]
#
# [Closing paragraph that connects this specific scenario to broader data engineering challenges that Prefect helps solve]
#
# To learn more about how Prefect can help with similar workflows, check out:
# - [Documentation link to related concept](https://docs.prefect.io/[concept-path])
# - [Documentation link to related concept](https://docs.prefect.io/[concept-path])
# - [Documentation link to related concept](https://docs.prefect.io/[concept-path])

if __name__ == "__main__":
    example_flow()
