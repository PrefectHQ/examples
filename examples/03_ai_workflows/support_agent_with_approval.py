# ---
# title: AI support agent with human approval
# description: Build a durable AI workflow - LLM calls with retries and caching, policy checks in code, a human approval step in the Prefect UI, and idempotent actions that never run twice.
# icon: robot
# dependencies: ["prefect"]
# cmd: ["python", "03_ai_workflows/support_agent_with_approval.py"]
# tags: [ai, agents, human_in_the_loop, retries, caching, transactions]
# draft: false
# ---
#
# An "agent" that triages customer support tickets:
#
# 1. **Drafts a reply** for each ticket with an LLM, in parallel.
#    LLM APIs are flaky (rate limits, overloaded errors), so the call has
#    [retries](https://docs.prefect.io/v3/develop/write-tasks#retries).
#    LLM calls are also slow and cost money, so results are
#    [cached](https://docs.prefect.io/v3/develop/task-caching): re-running the flow
#    does not pay for the same drafts twice.
# 2. **Applies policy in plain code, not in the prompt.** Low-risk actions run
#    automatically. Refunds over a threshold are flagged.
# 3. **Pauses for a human** on flagged tickets. The run waits, visible in the UI, until
#    a reviewer approves or rejects through a form generated from a
#    [`RunInput`](https://docs.prefect.io/v3/advanced/interactive) class.
# 4. **Executes each action exactly once.** Every ticket is handled inside a
#    [transaction](https://docs.prefect.io/v3/develop/transactions) keyed by ticket ID, so
#    re-running the flow never sends a second reply or issues a second refund.
#
# ## Running the example
#
# ```bash
# prefect server start            # terminal 1, then open http://127.0.0.1:4200
# python 03_ai_workflows/support_agent_with_approval.py   # terminal 2
# ```
#
# When the run pauses, open it in the UI, review the `approval-t-103` artifact, and click
# **Resume**. Keep the script running while it waits - that process continues the run.
#
# * By default the LLM is simulated (no API key, no cost) and every draft fails on its first
#   attempt, so you can watch retries happen. Set `ANTHROPIC_API_KEY` and
#   `pip install anthropic` to use Claude instead.
# * Set `CI=true` to auto-approve instead of pausing, for unattended runs.

from __future__ import annotations

import os
import random
import time
from datetime import timedelta

from prefect import flow, task
from prefect.artifacts import create_markdown_artifact, create_table_artifact
from prefect.cache_policies import INPUTS, TASK_SOURCE
from prefect.flow_runs import pause_flow_run
from prefect.input import RunInput
from prefect.runtime import task_run
from prefect.transactions import transaction

# Refunds above this amount need a human. This is the governance knob: it lives in
# code you can review and test, not in a prompt the model might ignore.
APPROVAL_THRESHOLD_USD = 100

SAMPLE_TICKETS = [
    {
        "id": "T-101",
        "customer": "Ana",
        "message": "How do I reset my password?",
        "refund_usd": 0,
    },
    {
        "id": "T-102",
        "customer": "Ben",
        "message": "I was double charged $25 this month.",
        "refund_usd": 25,
    },
    {
        "id": "T-103",
        "customer": "Cara",
        "message": "Your outage cost us a day. We want our $750 annual fee back.",
        "refund_usd": 750,
    },
]


# ## The LLM call
#
# Two backends: a simulated one for demos, and Claude when `ANTHROPIC_API_KEY` is set.


class SimulatedLLMError(Exception):
    """Stands in for the transient errors real LLM APIs return (429 / 529 overloaded)."""


def _simulated_llm(ticket: dict) -> str:
    time.sleep(1.5)  # LLM calls are slow - this is why caching matters
    fail_first = os.getenv("DEMO_FAIL_FIRST_ATTEMPT", "true") == "true"
    if fail_first and task_run.run_count == 1:
        raise SimulatedLLMError("529 Overloaded (simulated) - Prefect will retry")
    if random.random() < float(os.getenv("DEMO_FAILURE_RATE", "0")):
        raise SimulatedLLMError("429 Rate limited (simulated)")
    return (
        f"Hi {ticket['customer']}, thanks for reaching out about: "
        f'"{ticket["message"]}" We\'re on it and will follow up shortly.'
    )


def _claude(ticket: dict) -> str:
    import anthropic

    # max_retries=0: let Prefect own retries, so every attempt is visible in the UI.
    client = anthropic.Anthropic(max_retries=0)
    response = client.beta.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        output_config={"effort": "low"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # if the model declines, the API retries on a fallback model
        system=(
            "You are a customer support agent. Write a short, friendly reply to the "
            "ticket. Do not promise refunds or other actions - a separate system "
            "decides those."
        ),
        messages=[{"role": "user", "content": ticket["message"]}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError(f"Model declined to draft a reply for {ticket['id']}")
    return next(b.text for b in response.content if b.type == "text")


# ## Tasks
#
# `retries` handles flaky APIs. `cache_policy=INPUTS + TASK_SOURCE` means: same ticket
# and same code -> reuse the stored result instead of calling the LLM again.


@task(
    retries=3,
    retry_delay_seconds=[1, 2, 4],
    cache_policy=INPUTS + TASK_SOURCE,
    cache_expiration=timedelta(hours=1),
    persist_result=True,
    task_run_name="draft-reply-{ticket[id]}",
)
def draft_reply(ticket: dict) -> str:
    if os.getenv("ANTHROPIC_API_KEY"):
        return _claude(ticket)
    return _simulated_llm(ticket)


@task
def needs_approval(ticket: dict) -> bool:
    return ticket["refund_usd"] > APPROVAL_THRESHOLD_USD


@task(task_run_name="execute-{ticket[id]}")
def execute(ticket: dict, reply: str) -> None:
    # In real life: send the email, call the billing API to issue the refund, etc.
    print(f"[{ticket['id']}] Sent reply: {reply}")
    if ticket["refund_usd"]:
        print(f"[{ticket['id']}] Issued refund of ${ticket['refund_usd']}")


# ## Human in the loop
#
# `RunInput` defines the form the reviewer sees in the UI. `pause_flow_run` suspends the
# run until someone submits it. The run shows as "Paused" with a Resume button.


class ApprovalDecision(RunInput):
    approved: bool
    reviewer_note: str = ""


def request_approval(ticket: dict, reply: str) -> ApprovalDecision:
    if os.getenv("CI"):
        print(f"[{ticket['id']}] CI is set - auto-approving instead of pausing.")
        return ApprovalDecision(approved=True, reviewer_note="auto-approved (CI)")

    create_markdown_artifact(
        key=f"approval-{ticket['id'].lower()}",
        markdown=(
            f"## Approval needed: {ticket['id']}\n\n"
            f"**Customer:** {ticket['customer']}\n\n"
            f"**Ticket:** {ticket['message']}\n\n"
            f"**Requested refund:** ${ticket['refund_usd']} "
            f"(threshold ${APPROVAL_THRESHOLD_USD})\n\n"
            f"**Drafted reply:**\n\n> {reply}\n"
        ),
        description="Review the drafted reply and refund, then click Resume on the flow run.",
    )
    print(
        f"[{ticket['id']}] Waiting for human approval - "
        "open the flow run in the UI and click Resume."
    )
    return pause_flow_run(wait_for_input=ApprovalDecision, timeout=900)


# ## The flow
#
# Each ticket is handled inside `transaction(key=...)`. When the block finishes, Prefect
# writes a record under that key. On any later run, `txn.is_committed()` sees the record
# and the ticket is skipped: no second approval request, no second refund. This is the
# same idea as an idempotency key in a payments API.
#
# `batch_id` is part of the key. Pass a new value to process the same sample tickets again.


@flow(log_prints=True)
def support_agent(tickets: list[dict] | None = None, batch_id: str = "demo-1") -> None:
    tickets = tickets or SAMPLE_TICKETS

    # Draft every reply in parallel. Each one retries and caches on its own.
    drafts = draft_reply.map(tickets).result()

    outcomes = []
    for ticket, reply in zip(tickets, drafts):
        with transaction(key=f"support-agent/{batch_id}/{ticket['id']}") as txn:
            if txn.is_committed():
                print(f"[{ticket['id']}] Already handled in an earlier run - skipping.")
                outcomes.append({**ticket, "decision": "skipped (already handled)"})
                continue

            if needs_approval(ticket):
                decision = request_approval(ticket, reply)
                if not decision.approved:
                    print(f"[{ticket['id']}] Rejected: {decision.reviewer_note!r}")
                    txn.stage("rejected")
                    outcomes.append({**ticket, "decision": "rejected"})
                    continue
                label = f"approved by reviewer: {decision.reviewer_note}"
            else:
                label = "auto-approved"

            execute(ticket, reply)
            txn.stage(label)
            outcomes.append({**ticket, "decision": label})

    create_table_artifact(
        key="support-agent-summary",
        table=[
            {k: o[k] for k in ("id", "customer", "refund_usd", "decision")}
            for o in outcomes
        ],
        description="What the agent did, and who approved it.",
    )


if __name__ == "__main__":
    support_agent()

# ## What to show in a demo
#
# * **Retries:** every draft task shows a failed attempt, then success - without a
#   single try/except in the code.
# * **Parallelism:** the three drafts run at the same time (see the timeline).
# * **Human in the loop:** the run sits in "Paused". The approval artifact shows the
#   reviewer what they're approving. Resume opens a typed form (approved / reviewer_note).
# * **Exactly once:** run the script again. The drafts come back as "Cached" and every
#   ticket is skipped as already handled - no duplicate replies or refunds.
# * **Audit trail:** the summary table records what happened and who approved it.
