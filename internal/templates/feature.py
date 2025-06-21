# ---
# title: [Feature Name] – [Short Catchy Description with Emoji]
# description: Learn about Prefect's **[Feature]** – [brief description of what it does and why it matters].
# dependencies: ["prefect", "other_dependencies"]
# cmd: ["python", "[directory]/[filename].py"]
# tags: [relevant, tags, for, feature]
# ---

# ## [Feature Name] – [Short Catchy Description with Emoji]
#
# [One paragraph introduction to the feature and its importance in data workflows]
#
# [Feature] offers these key capabilities:
# * `[parameter/option]` – [Brief explanation of what it does and how to use it]
# * `[parameter/option]` – [Brief explanation of what it does and how to use it]
# * `[parameter/option]` – [Brief explanation of what it does and how to use it]
#
# ### When should you use [Feature]?
# * **[Use case]** – [Brief explanation of this use case]
# * **[Use case]** – [Brief explanation of this use case]
# * **[Use case]** – [Brief explanation of this use case]
# * **[Use case]** – [Brief explanation of this use case]
#
# ### [Comparison or Important Distinction] (if applicable)
# * **[Option A]** [explanation of how this option works]
# * **[Option B]** [explanation of how this option works]
#
# **Best practice**: [1-2 sentences about recommended approach]
#
# [Additional practical tips or context - 1-2 paragraphs]
#
# ### Running the example locally
# ```bash
# python [directory]/[filename].py
# ```
# [Brief explanation of what happens when you run the example]
#
# ## Code organization
# 1. **Imports & setup** – [Brief explanation of imports and setup]
# 2. **[Component 1]** – [Brief explanation of first major code component]
# 3. **[Component 2]** – [Brief explanation of second major code component]
# 4. **[Component 3]** – [Brief explanation of third major code component]
# 5. **Execution** – [Brief explanation of how the code runs]

from prefect import flow, task

# ---------------------------------------------------------------------------
# [Component 1 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [1-2 paragraphs explaining this component in detail]


def example_function():
    """Docstring explaining function purpose."""
    # Implementation
    pass


# ---------------------------------------------------------------------------
# [Component 2 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [1-2 paragraphs explaining this component in detail]


@task(retries=2, retry_delay_seconds=5)
def example_task():
    """Docstring explaining task purpose."""
    # Implementation
    pass


# ---------------------------------------------------------------------------
# [Component 3 - section heading with descriptive dashes] --------------------
# ---------------------------------------------------------------------------
# [1-2 paragraphs explaining this component in detail]


@flow(log_prints=True)
def example_flow(param1="default_value"):
    """
    [Flow docstring with clear explanation]
    """
    # Flow implementation
    pass


# ### What just happened?
# [Step-by-step explanation of what happens when the code runs]
#
# Here's the sequence of events:
# 1. [First step in the execution]
# 2. [Second step in the execution]
# 3. [Third step in the execution]
# 4. [Fourth step in the execution]
#
### [ Pick randomly between "Why This Is Important" or "Why This Matters" or something similar]
# **[Key insight or important takeaway]** [Brief explanation of why this matters]
#
# [Closing paragraph that summarizes the value proposition of the feature]

if __name__ == "__main__":
    example_flow()
