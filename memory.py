import os
import json
import threading
import urllib.request
from datetime import datetime

VAULT = os.path.join(os.path.dirname(__file__), "memory")
BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"


def _ensure_vault():
    os.makedirs(VAULT, exist_ok=True)


def _embed(text: str) -> list[float] | None:
    try:
        payload = json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE_URL}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))["embedding"]
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def save(role: str, content: str, tags: list[str] = []) -> str:
    _ensure_vault()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{ts}_{role}"

    tag_line = ", ".join(tags) if tags else "general"
    md = f"---\ntimestamp: {datetime.now().isoformat()}\nrole: {role}\ntags: {tag_line}\n---\n\n{content}\n"
    with open(os.path.join(VAULT, f"{stem}.md"), "w", encoding="utf-8") as f:
        f.write(md)

    if role != "system":
        vec = _embed(content)
        if vec:
            with open(os.path.join(VAULT, f"{stem}.json"), "w", encoding="utf-8") as f:
                json.dump({"role": role, "content": content, "embedding": vec}, f)

    return os.path.join(VAULT, f"{stem}.md")


def save_async(role: str, content: str, tags: list[str] = []) -> threading.Thread:
    """Save entry and generate embedding in a background thread — non-blocking."""
    t = threading.Thread(target=save, args=(role, content, tags), daemon=True)
    t.start()
    return t


def save_eval(score: int, reasoning: str, question: str = "", response: str = ""):
    """Store a quality evaluation for a response (separate from main vault entries)."""
    _ensure_vault()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "role": "eval",
        "score": score,
        "reasoning": reasoning,
        "question": question[:300],
        "response": response[:300],
        "timestamp": datetime.now().isoformat()
    }
    with open(os.path.join(VAULT, f"{ts}_eval.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_quality_stats() -> dict:
    """Return aggregate quality stats from stored evaluations."""
    scores = []
    for fname in os.listdir(VAULT):
        if not fname.endswith("_eval.json"):
            continue
        try:
            with open(os.path.join(VAULT, fname), encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data.get("score"), (int, float)):
                scores.append(data["score"])
        except Exception:
            continue

    if not scores:
        return {"avg": None, "count": 0, "trend": "no data yet"}

    avg = sum(scores) / len(scores)
    recent = scores[-5:]
    recent_avg = sum(recent) / len(recent)

    if len(scores) < 3:
        trend = "building baseline"
    elif recent_avg >= avg + 0.5:
        trend = "improving"
    elif recent_avg <= avg - 0.5:
        trend = "declining"
    else:
        trend = "stable"

    return {
        "avg": round(avg, 1),
        "recent_avg": round(recent_avg, 1),
        "count": len(scores),
        "trend": trend
    }


def load_recent(n: int = 10) -> list[dict]:
    _ensure_vault()
    files = sorted([f for f in os.listdir(VAULT) if f.endswith(".md")], reverse=True)[:n]
    entries = []
    for fname in reversed(files):
        with open(os.path.join(VAULT, fname), encoding="utf-8") as f:
            raw = f.read()
        lines = raw.split("\n")
        role = "unknown"
        content_lines = []
        in_content = False
        for line in lines:
            if line.startswith("role:"):
                role = line.split(":", 1)[1].strip()
            if in_content:
                content_lines.append(line)
            if line == "---" and not in_content and role != "unknown":
                in_content = True
        entries.append({"role": role, "content": "\n".join(content_lines).strip()})
    return entries


def _get_session_cutoff() -> str:
    """Return the filename timestamp prefix of the most recent session marker."""
    system_files = sorted([f for f in os.listdir(VAULT) if f.endswith("_system.md")])
    return system_files[-1][:15] if system_files else ""


def search_relevant(query: str, top_k: int = 5) -> list[dict]:
    """Hybrid retrieval: current session entries always first, past sessions fill remaining slots semantically."""
    _ensure_vault()
    query_vec = _embed(query)
    if not query_vec:
        return load_recent(top_k)

    cutoff = _get_session_cutoff()
    current_entries = []
    past_scored = []

    for fname in sorted(os.listdir(VAULT)):
        if not fname.endswith(".json") or fname.endswith("_eval.json"):
            continue
        try:
            with open(os.path.join(VAULT, fname), encoding="utf-8") as f:
                data = json.load(f)
            score = _cosine(query_vec, data["embedding"])
            entry = {"role": data["role"], "content": data["content"], "score": score}
            if cutoff and fname[:15] >= cutoff:
                current_entries.append(entry)
            else:
                past_scored.append(entry)
        except Exception:
            continue

    past_scored.sort(key=lambda x: x["score"], reverse=True)
    remaining = max(0, top_k - len(current_entries))
    return current_entries + past_scored[:remaining]


def summarize_vault(query: str = "") -> str:
    if query:
        entries = search_relevant(query, top_k=5)
        if not entries:
            return "No relevant memory found."
        lines = []
        for e in entries:
            snippet = e["content"][:120] + "..." if len(e["content"]) > 120 else e["content"]
            lines.append(f"- past {e['role']} (relevance {e.get('score', 0):.2f}): {snippet}")
        return "PAST SESSION MEMORY (context only — do not copy this format into your response):\n" + "\n".join(lines)

    # Session-aware fallback (used by 'memory' command)
    entries = load_recent(10)
    if not entries:
        return "No memory yet."

    last_marker = -1
    for i, e in enumerate(entries):
        if e["role"] == "system" and "NEW SESSION" in e["content"]:
            last_marker = i

    lines = []
    for i, e in enumerate(entries):
        if e["role"] == "system":
            lines.append("=== NEW SESSION ===")
            continue
        label = "[CURRENT SESSION]" if i > last_marker else "[PREVIOUS SESSION]"
        snippet = e["content"][:120] + "..." if len(e["content"]) > 120 else e["content"]
        lines.append(f"{label} [{e['role'].upper()}]: {snippet}")
    return "\n".join(lines)
