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

# In-memory session buffer — injected into every prompt regardless of async save state.
# Prevents the race condition where a follow-up query arrives before the previous
# exchange has been written and embedded to the vault.
_session_buffer: list[dict] = []

# Holds the best result from the most recent research: run so task: can ground itself in it.
_last_research_best: dict | None = None

TASK_PLANNER_SYSTEM = (
    "You are a task planner. Given a goal, respond with ONLY a valid JSON array of 3-5 "
    "concrete step strings. No explanation, no markdown fences, just the JSON array. "
    'Example: ["Step 1: Research X", "Step 2: Analyse Y", "Step 3: Summarise findings"]'
)

STRATEGY_TASK_PLANNER_SYSTEM = (
    "You are a task planner. You will be given a specific research strategy with identified tactics, "
    "mechanisms, and platforms. Your job is to plan execution steps grounded STRICTLY in those tactics. "
    "Do NOT generate generic content. Do NOT invent new tactics. "
    "Read the strategy carefully, extract the specific tactics (e.g. quizzes, polls, share-to-earn, "
    "viral loops, FOMO triggers, referral systems) and plan steps that use ONLY those tactics. "
    "Every step must directly reference a specific tactic named in the strategy. "
    "Respond with ONLY a valid JSON array of 3-5 concrete step strings. "
    'Example: ["Day 1: Instagram Story quiz - What is your productivity type? (viral loop tactic)", '
    '"Day 2: Reel showing quiz results + CTA to share for FOMO", '
    '"Day 3: Share-to-earn post - tag 3 friends to unlock premium feature"]'
)

EVAL_SYSTEM = (
    "You are a quality evaluator for AI responses. Rate the response on accuracy, "
    "completeness, and clarity. Reply with ONLY valid JSON: "
    "{\"score\": N, \"reasoning\": \"one sentence\"} where N is an integer from 1 to 10."
)

PROFESSOR_PERSONA = (
    "You are a Professor of Social Media Marketing Strategy with 20 years of experience. "
    "Your expertise spans virality mechanics and viral loop design, guerrilla marketing tactics, "
    "emerging platform trends (TikTok, Threads, Instagram, YouTube Shorts), psychological triggers "
    "in social media (FOMO, social proof, identity signaling, novelty), and data-driven campaign "
    "optimization. When solving marketing problems, you think in terms of reach, resonance, and "
    "conversion. You are direct, strategic, and back every recommendation with a specific example "
    "or real-world tactic."
)

APPROACH_GENERATOR_SYSTEM = (
    "You are a Professor of Social Media Marketing Strategy. "
    "Given a marketing goal, generate exactly 3 DIFFERENT strategic approaches. "
    "Each approach must use a distinct marketing philosophy: "
    "one focused on virality, one on guerrilla tactics, one on trend-jacking. "
    "Reply with ONLY a valid JSON array of exactly 3 strings. "
    "Each string is one sentence naming and describing the approach. "
    'Example: ["Approach 1: Viral loop - ...", "Approach 2: Guerrilla - ...", "Approach 3: Trend-jack - ..."]'
)

MULTI_DIM_EVAL_SYSTEM = (
    "You are a Professor of Social Media Marketing Strategy evaluating a campaign approach. "
    "Score it on THREE separate dimensions. "
    "Reply with ONLY valid JSON: "
    "{\"strategic_quality\": N, \"feasibility\": N, \"viral_potential\": N, \"reasoning\": \"one sentence\"} "
    "where each N is an integer from 1 to 10."
)

CRITIC_EVAL_SYSTEM = (
    "You are a skeptical marketing critic. Your job is to find weaknesses, not strengths. "
    "Score this approach harshly on how realistic and achievable it actually is in practice. "
    "Reply with ONLY valid JSON: {\"score\": N, \"reasoning\": \"one sentence\"} "
    "where N is an integer from 1 to 10. Be critical and demanding."
)

TIEBREAKER_SYSTEM = (
    "You are a senior marketing strategist making a final decision between two approaches. "
    "Pick the one more likely to succeed in the real world. "
    "Reply with ONLY valid JSON: {\"winner\": N, \"reasoning\": \"one sentence\"} "
    "where N is 1 or 2."
)

REFINEMENT_GENERATOR_SYSTEM = (
    "You are a Professor of Social Media Marketing Strategy. "
    "Given the best-performing approach from a previous research round, generate exactly 3 REFINED variations. "
    "Each variation must improve on a different weakness: "
    "one improves feasibility, one improves viral potential, one improves strategic depth. "
    "Reply with ONLY a valid JSON array of exactly 3 strings. No titles, no sub-items, no numbering inside strings. "
    "Each string is ONE complete sentence that names and describes the full refined approach. "
    'Example: ["Refined feasibility: ...", "Refined viral: ...", "Refined strategic: ..."]'
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
        if _session_buffer:
            live = "\n".join(
                f"{e['role'].capitalize()}: {e['content'][:300]}"
                for e in _session_buffer[-4:]
            )
            context = "LIVE SESSION (most recent exchanges):\n" + live + "\n\n" + context
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


def evaluate_approach_dual(approach: str, response: str) -> dict:
    """Dual evaluation: multi-dimension professor scoring + adversarial critic scoring."""
    eval_prompt = f"Approach: {approach}\n\nFull strategy: {response}"

    strategic, feasibility, viral = 5, 5, 5
    try:
        raw = ask_hermes(eval_prompt, system_override=MULTI_DIM_EVAL_SYSTEM, use_memory=False)
        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            strategic = int(data.get("strategic_quality", 5))
            feasibility = int(data.get("feasibility", 5))
            viral = int(data.get("viral_potential", 5))
    except Exception:
        pass

    prof_avg = round((strategic + feasibility + viral) / 3, 2)

    critic_score = 5
    try:
        raw2 = ask_hermes(eval_prompt, system_override=CRITIC_EVAL_SYSTEM, use_memory=False)
        match2 = re.search(r'\{[^}]+\}', raw2, re.DOTALL)
        if match2:
            data2 = json.loads(match2.group())
            critic_score = int(data2.get("score", 5))
    except Exception:
        pass

    composite = round((prof_avg + critic_score) / 2, 2)
    return {
        "strategic_quality": strategic,
        "feasibility": feasibility,
        "viral_potential": viral,
        "prof_avg": prof_avg,
        "critic_score": critic_score,
        "composite": composite,
    }


def _head_to_head(a: dict, b: dict) -> dict:
    """Run a direct comparison between two tied approaches and return the winner."""
    prompt = (
        f"Approach 1: {a['approach']}\nStrategy 1: {a['response'][:500]}\n\n"
        f"Approach 2: {b['approach']}\nStrategy 2: {b['response'][:500]}"
    )
    try:
        raw = ask_hermes(prompt, system_override=TIEBREAKER_SYSTEM, use_memory=False)
        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            winner_num = int(data.get("winner", 1))
            reasoning = data.get("reasoning", "")
            winner = a if winner_num == 1 else b
            print(f"  [TIEBREAKER] Winner: {winner['approach'][:60]}... | {reasoning}")
            return winner
    except Exception:
        pass
    return a


def _select_best(results: list) -> dict:
    """Select best result by composite score. Runs head-to-head only when the top 2 scores are within 0.5 points."""
    sorted_results = sorted(results, key=lambda x: x["composite"], reverse=True)
    if (len(sorted_results) > 1
            and abs(sorted_results[0]["composite"] - sorted_results[1]["composite"]) <= 0.5):
        s0 = sorted_results[0]["composite"]
        s1 = sorted_results[1]["composite"]
        print(f"  [TIE] Top 2 within 0.5 pts ({s0:.1f} vs {s1:.1f}) - running head-to-head...")
        return _head_to_head(sorted_results[0], sorted_results[1])
    return sorted_results[0]


def run_autoresearch_loop(goal: str, max_iterations: int = 3, quality_threshold: float = 8.0):
    print(f"\n[AUTORESEARCH] Goal: {goal}")
    print(f"[AUTORESEARCH] Max iterations: {max_iterations} | Quality threshold: {quality_threshold}/10")
    print("[AUTORESEARCH] Evaluation: Professor multi-dim + Critic adversarial (dual scoring)")
    print("[AUTORESEARCH] Selection: Composite score + head-to-head tiebreaker\n")

    best_overall = None
    best_overall_score = 0.0
    iteration = 0

    for iteration in range(1, max_iterations + 1):
        print("=" * 60)
        print(f"[ITERATION {iteration}/{max_iterations}]")

        if iteration == 1:
            print("[AUTORESEARCH] Generating 3 distinct approaches...\n")
            raw = ask_hermes(goal, system_override=APPROACH_GENERATOR_SYSTEM, use_memory=False)
        else:
            print(f"[AUTORESEARCH] Refining best approach (score: {best_overall_score}/10)...\n")
            refine_prompt = (
                f"Goal: {goal}\n\n"
                f"Best approach from previous round:\n{best_overall['approach']}\n\n"
                f"Best strategy from previous round:\n{best_overall['response']}\n\n"
                f"Composite score: {best_overall_score}/10"
            )
            raw = ask_hermes(refine_prompt, system_override=REFINEMENT_GENERATOR_SYSTEM, use_memory=False)

        try:
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            approaches = json.loads(match.group()) if match else [raw]
            # Flatten nested case: model returned a JSON array as a string inside an outer array
            if len(approaches) == 1 and isinstance(approaches[0], str):
                try:
                    inner = json.loads(approaches[0].strip())
                    if isinstance(inner, list) and len(inner) > 1:
                        approaches = inner
                except Exception:
                    pass
        except Exception:
            approaches = [raw]
        if len(approaches) < 2:
            approaches = [raw]
        approaches = approaches[:3]  # Hard cap — model sometimes returns title+description as separate items

        print(f"[AUTORESEARCH] {len(approaches)} approach{'es' if len(approaches) != 1 else ''} for iteration {iteration}:")
        for i, a in enumerate(approaches, 1):
            print(f"  {i}. {a}")
        print()

        results = []
        for i, approach in enumerate(approaches, 1):
            print(f"[APPROACH {i}/{len(approaches)}] Executing: {approach[:80]}...")

            execution_prompt = (
                f"Goal: {goal}\n\n"
                f"Strategy to develop: {approach}\n\n"
                f"Develop this approach fully with specific tactics, platform recommendations, "
                f"content ideas, and expected outcomes. Be concrete and practical."
            )
            response = ask_hermes(execution_prompt, system_override=PROFESSOR_PERSONA, use_memory=False)
            print(f"\n{response}\n")

            scores = evaluate_approach_dual(approach, response)
            composite = scores["composite"]
            print(
                f"  [Prof avg: {scores['prof_avg']:.1f}/10 | Critic: {scores['critic_score']}/10 | "
                f"Composite: {composite:.1f}/10]\n"
                f"  Strategic: {scores['strategic_quality']} | "
                f"Feasibility: {scores['feasibility']} | "
                f"Viral: {scores['viral_potential']}\n"
            )

            results.append({
                "approach": approach,
                "response": response,
                "scores": scores,
                "composite": composite,
                "iteration": iteration,
            })

            memory.save_async(
                "autoresearch",
                f"Goal: {goal}\nIteration {iteration}, Approach {i}: {approach}\n"
                f"Response: {response}\nComposite: {composite:.1f}/10",
                tags=["autoresearch", f"iter_{iteration}", f"approach_{i}"]
            )

        best_this_round = _select_best(results)
        best_idx = results.index(best_this_round) + 1
        round_score = best_this_round["composite"]

        print(f"\n[ITERATION {iteration} RESULTS]")
        for i, r in enumerate(results, 1):
            marker = "  <-- BEST" if i == best_idx else ""
            print(f"  Approach {i}: {r['composite']:.1f}/10{marker}")

        if round_score > best_overall_score:
            best_overall = best_this_round
            best_overall_score = round_score
            print(f"[NEW BEST] Iteration {iteration}, Approach {best_idx}: {best_overall_score:.1f}/10\n")

        if best_overall_score >= quality_threshold:
            print(f"[AUTORESEARCH] Threshold {quality_threshold}/10 reached. Stopping.\n")
            break
        elif iteration < max_iterations:
            print(
                f"[AUTORESEARCH] Score {best_overall_score:.1f}/10 below threshold. "
                f"Running iteration {iteration + 1}...\n"
            )

    print("=" * 60)
    print(f"[AUTORESEARCH COMPLETE] {iteration} iteration(s) | Best composite: {best_overall_score:.1f}/10")
    print("=" * 60)
    print(best_overall["response"])
    print()

    comparison = (
        f"Goal: {goal}\n"
        f"Iterations run: {iteration} | Best composite: {best_overall_score:.1f}/10\n"
        f"Best approach: {best_overall['approach']}\n\n"
        f"{best_overall['response']}"
    )
    memory.save_async("autoresearch_best", comparison, tags=["autoresearch", "best_result"])
    print("[AUTORESEARCH] Final result saved to vault.\n")

    global _last_research_best
    _last_research_best = best_overall


def run_task_loop(goal: str):
    print(f"\n[AGENT] Decomposing goal: {goal}\n")

    if _last_research_best:
        strategy_context = (
            f"Approach: {_last_research_best['approach']}\n\n"
            f"Full strategy:\n{_last_research_best['response'][:1200]}"
        )
        enriched_goal = (
            f"Strategy from AutoResearch to execute:\n{strategy_context}\n\n"
            f"STRICT REQUIREMENT: Use ONLY the specific tactics from this strategy "
            f"(e.g. quizzes, polls, share-to-earn, viral loops, FOMO). "
            f"Do NOT create generic content. Every step must reference a named tactic from the strategy.\n\n"
            f"Task: {goal}"
        )
        planner_system = STRATEGY_TASK_PLANNER_SYSTEM
    elif _session_buffer:
        recent = "\n".join(
            f"{e['role'].capitalize()}: {e['content'][:300]}"
            for e in _session_buffer[-4:]
        )
        enriched_goal = f"Recent session context:\n{recent}\n\nTask to plan: {goal}"
        planner_system = TASK_PLANNER_SYSTEM
    else:
        enriched_goal = goal
        planner_system = TASK_PLANNER_SYSTEM

    plan_raw = ask_hermes(enriched_goal, system_override=planner_system, use_memory=False)

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
        if _last_research_best:
            step_prompt = (
                f"Strategy context:\n{strategy_context}\n\n"
                f"Task: {task}\n\n"
                f"Execute this task using ONLY the specific tactics from the strategy above. "
                f"Reference the actual tactics by name. Be concrete and actionable."
            )
            result = ask_hermes(step_prompt, use_memory=False)
        else:
            result = ask_hermes(task)
        result = re.sub(r'^\[[A-Z]+\]\s*', '', result).strip()
        print(f"\n{result}\n")
        results.append({"task": task, "result": result})
        memory.save_async("agent", f"Task: {task}\nResult: {result}", tags=["task_loop", f"step_{i}"])

    synthesis_prompt = (
        f"Goal: {goal}\n\n"
        + "\n".join(f"Step {i+1}: {r['task']}\nResult: {r['result']}" for i, r in enumerate(results))
        + "\n\nProvide a concise final summary of what was accomplished, "
        + "referencing the specific tactics that were executed."
    )
    final = ask_hermes(synthesis_prompt, use_memory=False)
    final = re.sub(r'^\[[A-Z]+\]\s*', '', final).strip()
    print(f"[AGENT COMPLETE]\n{final}\n")
    memory.save_async("agent_summary", f"Goal: {goal}\nSummary: {final}", tags=["summary"])

    # Evaluate the final synthesis in background
    threading.Thread(
        target=evaluate_response,
        args=(goal, final),
        daemon=True
    ).start()


def run():
    global _session_buffer, _last_research_best
    _session_buffer = []
    _last_research_best = None

    print("\n=== Hermes + Rowboat Dual-Layer AI Environment ===")
    print("Hermes  : reasoning engine (Nous Research via Ollama)")
    print("Rowboat : semantic memory layer (local Markdown vault + embeddings)")
    print("Commands : 'memory' | 'task: <goal>' | 'research: <goal>' | 'quit'\n")

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
            print("Exiting.")
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
        if user_input.lower().startswith("research:"):
            goal = user_input[9:].strip()
            if goal:
                run_autoresearch_loop(goal)
            continue

        # Save user message in background (parallel — doesn't block response)
        memory.save_async("user", user_input, tags=["input"])
        _session_buffer.append({"role": "user", "content": user_input})

        print("Hermes: ", end="", flush=True)
        response = ask_hermes(user_input)
        response = re.sub(r'^\[[A-Z]+\]\s*', '', response).strip()
        print(response)

        _session_buffer.append({"role": "hermes", "content": response})

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
