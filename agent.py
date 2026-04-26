import json
import re
import threading
import urllib.request
import memory

CONFIG = json.load(open("config.json", encoding="utf-8"))
HERMES = CONFIG["hermes"]
BASE_URL = HERMES["base_url"]

# Wire memory module to config
memory.BASE_URL = BASE_URL
memory.EMBED_MODEL = HERMES.get("embed_model", "nomic-embed-text")

TASK_PLANNER_SYSTEM = (
    "You are a task planner. Given a goal, respond with ONLY a valid JSON array of 3-5 "
    "concrete step strings. No explanation, no markdown fences, just the JSON array. "
    'Example: ["Step 1: Research X", "Step 2: Analyse Y", "Step 3: Summarise findings"]'
)

EVAL_SYSTEM = (
    "You are a quality evaluator for AI responses. Rate the response on accuracy, "
    "completeness, and clarity. Reply with ONLY valid JSON: "
    "{\"score\": N, \"reasoning\": \"one sentence\"} where N is an integer from 1 to 10."
)


def build_system_prompt() -> str:
    """Return system prompt, dynamically adjusted based on quality trend."""
    base = HERMES["system_prompt"]
    stats = memory.get_quality_stats()
    if stats["count"] >= 3 and stats["avg"] is not None:
        if stats["avg"] < 6.0:
            base += (
                f"\n\nSelf-improvement note: Your recent responses have averaged "
                f"{stats['avg']}/10 in quality. Focus on being more thorough, accurate, "
                f"and complete in your answers."
            )
        elif stats["avg"] >= 8.5:
            base += (
                f"\n\nSelf-improvement note: Your recent responses have averaged "
                f"{stats['avg']}/10. Maintain this standard."
            )
    return base


def ask_hermes(user_input: str, system_override: str = None, use_memory: bool = True) -> str:
    if use_memory:
        context = memory.summarize_vault(query=user_input)
        system_content = (system_override or build_system_prompt()) + "\n\n--- RELEVANT MEMORY CONTEXT ---\n" + context
    else:
        system_content = system_override or build_system_prompt()

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_input}
    ]

    payload = json.dumps({
        "model": HERMES["model"],
        "messages": messages,
        "stream": False,
        "options": {"temperature": HERMES["temperature"]}
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"]


def evaluate_response(question: str, response: str):
    """Ask Hermes to self-evaluate a response and store the score."""
    prompt = f"Question: {question}\n\nResponse: {response}"
    try:
        raw = ask_hermes(prompt, system_override=EVAL_SYSTEM, use_memory=False)
        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = int(data.get("score", 5))
            reasoning = data.get("reasoning", "")
            memory.save_eval(score, reasoning, question=question, response=response)
            return score, reasoning
    except Exception:
        pass
    return None, None


def run_task_loop(goal: str):
    print(f"\n[AGENT] Decomposing goal: {goal}\n")

    plan_raw = ask_hermes(goal, system_override=TASK_PLANNER_SYSTEM, use_memory=False)

    try:
        match = re.search(r'\[.*?\]', plan_raw, re.DOTALL)
        tasks = json.loads(match.group()) if match else [goal]
    except Exception:
        tasks = [goal]

    print(f"[AGENT] {len(tasks)} steps planned:")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t}")
    print()

    results = []
    for i, task in enumerate(tasks, 1):
        print(f"[STEP {i}/{len(tasks)}] {task}")
        result = ask_hermes(task)
        print(f"  -> {result[:200]}{'...' if len(result) > 200 else ''}\n")
        results.append({"task": task, "result": result})
        memory.save_async("agent", f"Task: {task}\nResult: {result}", tags=["task_loop", f"step_{i}"])

    synthesis_prompt = (
        f"Goal: {goal}\n\n"
        + "\n".join(f"Step {i+1}: {r['task']}\nResult: {r['result']}" for i, r in enumerate(results))
        + "\n\nProvide a concise final summary of what was accomplished."
    )
    final = ask_hermes(synthesis_prompt, use_memory=False)
    print(f"[AGENT COMPLETE]\n{final}\n")
    memory.save_async("agent_summary", f"Goal: {goal}\nSummary: {final}", tags=["summary"])

    # Evaluate the final synthesis in background
    threading.Thread(
        target=evaluate_response,
        args=(goal, final),
        daemon=True
    ).start()


def run():
    print("\n=== Hermes + Rowboat Dual-Layer AI Environment ===")
    print("Hermes  : reasoning engine (Nous Research via Ollama)")
    print("Rowboat : semantic memory layer (local Markdown vault + embeddings)")
    print("Commands : 'memory' | 'task: <goal>' | 'quit'\n")

    memory.save("system", "--- NEW SESSION STARTED ---", tags=["session_marker"])

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Saving session and exiting.")
            break
        if user_input.lower() == "memory":
            print("\n--- MEMORY VAULT (session view) ---")
            print(memory.summarize_vault())
            stats = memory.get_quality_stats()
            if stats["count"] > 0:
                print(f"\n--- QUALITY STATS ---")
                print(f"Evaluations : {stats['count']}")
                print(f"Average     : {stats['avg']}/10")
                print(f"Recent avg  : {stats['recent_avg']}/10")
                print(f"Trend       : {stats['trend']}")
            print("---\n")
            continue
        if user_input.lower().startswith("task:"):
            goal = user_input[5:].strip()
            if goal:
                run_task_loop(goal)
            continue

        # Save user message in background (parallel — doesn't block response)
        memory.save_async("user", user_input, tags=["input"])

        print("Hermes: ", end="", flush=True)
        response = ask_hermes(user_input)
        print(response)

        # Save response and run evaluation — both in background threads
        memory.save_async("hermes", response, tags=["response"])
        threading.Thread(
            target=evaluate_response,
            args=(user_input, response),
            daemon=True
        ).start()

        print()


if __name__ == "__main__":
    run()
