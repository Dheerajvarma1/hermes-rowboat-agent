from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# Page margins
for section in doc.sections:
    section.top_margin    = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin   = Inches(1.2)
    section.right_margin  = Inches(1.2)

# ── Helpers ───────────────────────────────────────────────────────────────────

def set_font(run, size=11, bold=False):
    run.font.name = "Calibri"
    run.font.size = Pt(size)
    run.font.bold = bold

def add_divider():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(2)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    pBdr.append(bottom)
    pPr.append(pBdr)

def add_title_block():
    p1 = doc.add_paragraph()
    r1 = p1.add_run("Plan Document")
    set_font(r1, size=12, bold=True)
    p1.paragraph_format.space_after = Pt(4)

    p2 = doc.add_paragraph()
    r2 = p2.add_run("Hermes + Rowboat: Dual-Layer AI Environment")
    set_font(r2, size=14, bold=True)
    p2.paragraph_format.space_after = Pt(2)

    p3 = doc.add_paragraph()
    r3 = p3.add_run("Semantic Memory Retrieval & Autonomous Task Execution")
    set_font(r3, size=11, bold=False)
    p3.paragraph_format.space_after = Pt(8)

def add_section_heading(number, text):
    add_divider()
    p = doc.add_paragraph()
    run = p.add_run(f"{number}. {text}")
    set_font(run, size=11, bold=True)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after  = Pt(4)

def add_sub_heading(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, size=11, bold=True)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)

def add_body(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_font(run, size=11)
    p.paragraph_format.space_after = Pt(4)

def add_bullet(text):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    set_font(run, size=11)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.space_after = Pt(2)

def add_workflow(steps):
    p = doc.add_paragraph()
    run = p.add_run(steps)
    set_font(run, size=10.5)
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_after = Pt(4)

def add_label_value(label, value):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.4)
    p.paragraph_format.space_after = Pt(2)
    r1 = p.add_run(f"{label}:  ")
    set_font(r1, size=11, bold=True)
    r2 = p.add_run(value)
    set_font(r2, size=11)

def add_diagram_box(text):
    """Render ASCII diagram in a shaded monospace box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    # Light gray background
    shading = OxmlElement("w:shd")
    shading.set(qn("w:val"),   "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"),  "F2F2F2")
    cell.paragraphs[0]._p.get_or_add_pPr().append(shading)
    cell.paragraphs[0].clear()
    for line in text.split("\n"):
        p = cell.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after  = Pt(0)
        run = p.add_run(line)
        run.font.name = "Courier New"
        run.font.size = Pt(8.5)
    # Remove the blank first paragraph added automatically
    first = cell.paragraphs[0]
    if not first.text:
        first._element.getparent().remove(first._element)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

def add_simple_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    # Header row - bold text, white background
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        for para in hdr_cells[i].paragraphs:
            for run in para.runs:
                set_font(run, size=10.5, bold=True)

    # Data rows - plain text, no shading
    for ri, row in enumerate(rows):
        cells = table.rows[ri + 1].cells
        for ci, val in enumerate(row):
            cells[ci].text = val
            for para in cells[ci].paragraphs:
                for run in para.runs:
                    set_font(run, size=10.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT BODY
# ══════════════════════════════════════════════════════════════════════════════

add_title_block()

# 1. Objective
add_section_heading("1", "Objective of the System")
for b in [
    "To build a fully local AI agent that reasons, remembers, and improves across sessions.",
    "To enable the agent to retrieve semantically relevant memory - not just recent messages - on every query.",
    "To allow the agent to autonomously decompose a goal into steps, execute each step, and synthesise a final answer.",
    "To implement a self-evaluation feedback loop that scores every response and adapts the system prompt over time.",
    "To run entirely on local hardware with no API keys, no cloud dependency, and no pip installs.",
    "To align the system with the AutoResearch, Covenant, and prima.cpp concepts.",
]:
    add_bullet(b)

# 2. Concept
add_section_heading("2", "Concept of the System")
add_body(
    "The system functions as a dual-layer AI environment. Instead of acting as a single-turn chatbot, "
    "the system maintains persistent memory, plans tasks, and improves its reasoning over time."
)
add_body("Instead of only answering questions, the system:")
for b in [
    "Retrieves relevant context from past sessions before every response",
    "Decomposes goals into executable steps autonomously",
    "Stores every exchange as a searchable embedding",
    "Evaluates its own responses and adjusts its behavior accordingly",
    "Runs all inference locally - no data leaves the device",
]:
    add_bullet(b)

# 3. Vision
add_section_heading("3", "Vision of the System")
add_body(
    "The vision is to create a self-improving autonomous agent that acts like an AI researcher - "
    "one that reads its own notes before answering, grades its own work after answering, "
    "and adjusts how it reasons based on those grades. "
    "The system is a foundation for future multi-agent and distributed memory architectures."
)

# 4. Components
add_section_heading("4", "System Components")
add_simple_table(
    ["Role", "Component", "What It Does"],
    [
        ["Thinking",    "Hermes 3 (Nous Research via Ollama)", "Reasons, plans tasks, generates responses, self-evaluates"],
        ["Remembering", "Semantic Vault (Markdown + JSON)",    "Stores every exchange as a searchable embedding vector"],
        ["Improving",   "Evaluation Loop (Background Thread)", "Scores every response 1-10 and adapts the system prompt"],
    ]
)

add_sub_heading("Layer 1 - Reasoning Engine (Hermes 3)")
add_simple_table(
    ["Property", "Value"],
    [
        ["Model",    "hermes3 (Nous Research)"],
        ["Runtime",  "Ollama - local REST API"],
        ["Endpoint", "http://localhost:11434/api/chat"],
        ["Size",     "4.3 GB"],
        ["Role",     "Reasoning, task planning, synthesis, self-evaluation"],
    ]
)

add_sub_heading("Persona-Standardized Execution")
add_body(
    "Planning and execution quality is standardized through a fixed persona system. "
    "Rather than relying on ad-hoc prompting, every research task is routed through a dedicated "
    "Professor of Social Media Marketing persona. This ensures consistent reasoning depth, "
    "terminology, and strategic framing across all generated approaches, regardless of how the "
    "user phrases the goal."
)
for b in [
    "PROFESSOR_PERSONA: the execution engine for all research approaches - provides consistent strategic framing",
    "APPROACH_GENERATOR_SYSTEM: enforces three distinct marketing philosophies (viral, guerrilla, trend-jack)",
    "REFINEMENT_GENERATOR_SYSTEM: refines along three fixed improvement axes (feasibility, viral potential, strategic depth)",
    "Evaluation personas (MULTI_DIM_EVAL_SYSTEM, CRITIC_EVAL_SYSTEM) apply opposing but consistent scoring frameworks",
    "Result: persona-driven execution produces comparable, scoreable outputs rather than free-form narratives",
]:
    add_bullet(b)

add_sub_heading("Layer 2 - Semantic Memory Vault")
add_simple_table(
    ["Property", "Value"],
    [
        ["Storage format",   "Markdown (.md) + JSON embedding vectors (.json)"],
        ["Embedding model",  "nomic-embed-text (Ollama)"],
        ["Retrieval method", "Hybrid - current session entries first, then cosine similarity for past sessions"],
        ["Retrieval depth",  "Top-5 total: all current session entries + semantic matches from past sessions"],
        ["Session tracking", "Session marker written at startup"],
        ["Eval storage",     "Separate _eval.json files"],
    ]
)

add_sub_heading("Layer 3 - Evaluation and Adaptation")
add_simple_table(
    ["Property", "Value"],
    [
        ["Evaluator",    "Hermes 3 (same model, separate prompt)"],
        ["Score range",  "1-10 per response"],
        ["Trigger",      "Background thread after every response"],
        ["Adaptation",   "System prompt updated when average < 6.0 or >= 8.5"],
        ["Stats visible","Via memory command - count, average, trend"],
    ]
)

# 4 continued - Architecture Diagrams
add_sub_heading("Component Overview")
add_body("The diagram below shows how the three layers connect and communicate.")
add_diagram_box(
    "  USER INPUT (Terminal)\n"
    "        |\n"
    "        v\n"
    "+----------------------------------------------------+\n"
    "|          agent.py  -  Orchestration                |\n"
    "|                                                    |\n"
    "|  search_relevant()     build_system_prompt()       |\n"
    "|  run_task_loop()       save_async()       [bg]     |\n"
    "|  run_autoresearch_loop()                           |\n"
    "|  evaluate_approach_dual()   _select_best()         |\n"
    "|  _head_to_head()       evaluate_response() [bg]    |\n"
    "+----------+-------------------------------+---------+\n"
    "           |                               |\n"
    "           v                               v\n"
    "+--------------------+     +---------------------------+\n"
    "| LAYER 2 - VAULT    |     | LAYER 1 - HERMES 3        |\n"
    "|                    |<----| hermes3 via Ollama        |\n"
    "| .md  text files    |     | localhost:11434           |\n"
    "| .json embeddings   |     |                           |\n"
    "| _eval.json scores  |     | Active personas:          |\n"
    "| nomic-embed-text   |     |   PROFESSOR_PERSONA       |\n"
    "+--------------------+     |   MULTI_DIM_EVAL_SYSTEM   |\n"
    "                           |   CRITIC_EVAL_SYSTEM      |\n"
    "                           |   TIEBREAKER_SYSTEM       |\n"
    "                           |   REFINEMENT_GENERATOR    |\n"
    "                           +---------------------------+"
)

add_sub_heading("Logical Flow")
add_body("The diagram below shows the decision path taken for each type of user input.")
add_diagram_box(
    "                [ User Input ]\n"
    "                       |\n"
    "     +---------+--------+--------+---------+\n"
    "     |         |                 |         |\n"
    "  task:    research:           memory   message\n"
    "     |         |                 |         |\n"
    "     v         v                 v         v\n"
    " [Task    [Iteration N:       [Vault   [Embed Query]\n"
    "  Planner] Generate 3          View]        |\n"
    "     |     Approaches]                [search_relevant()]\n"
    "     v         |                            |\n"
    " [Execute   [Execute each            [Top-5 Entries]\n"
    "  Steps ]    w/ Professor]                  |\n"
    "     |         |                   [build_system_prompt()]\n"
    "     v         v                            |\n"
    " [Synthesis] [evaluate_approach_dual]  [ask_hermes()]\n"
    "     |        Prof avg + Critic             |\n"
    "     v         |                     [Response to User]\n"
    " [Evaluate]  [_select_best()]               |\n"
    " [bg thread]  Composite score         +-----+------+\n"
    "              + tiebreaker            |            |\n"
    "                   |            [save_async] [evaluate_resp]\n"
    "             [Score >= 8.0?]    [bg thread]  [bg thread]\n"
    "              Y          N           |            |\n"
    "              |          |      [.md+.json]  [_eval.json]\n"
    "           [Store    [REFINEMENT\n"
    "            Best]    Generate 3\n"
    "                     Variations\n"
    "                     -> Round N+1]"
)

# 5. Overall Workflow
add_section_heading("5", "Overall Workflow of the System")
add_workflow(
    "User Input\n"
    "  -> Embed query using nomic-embed-text\n"
    "  -> Cosine similarity search across vault\n"
    "  -> Select top-5 most relevant entries\n"
    "  -> Assemble prompt: base + quality note + memory context\n"
    "  -> Hermes generates response\n"
    "  -> Response shown to user immediately\n"
    "  -> Background Thread 1: save response + generate embedding\n"
    "  -> Background Thread 2: self-evaluate response (score 1-10)\n"
    "  -> Vault updated with .md + .json + _eval.json files\n"
    "  -> System prompt adapts on next query based on score trend"
)

# 6. Task Loop
add_section_heading("6", "Task Loop Workflow")
add_body("The task loop is triggered by prefixing any message with 'task:'. It enables the agent to operate autonomously across multiple steps.")

add_sub_heading("Step 1: Goal Received")
for b in [
    "User types: task: <goal>",
    "The system recognises the task prefix and routes to run_task_loop()",
]:
    add_bullet(b)
add_label_value("Example", "task: Compare supervised and unsupervised learning with real-world examples")

add_sub_heading("Step 2: Task Planning")
for b in [
    "Hermes receives the goal with a strict JSON planner prompt",
    "Returns a JSON array of 3-5 concrete step strings",
    "Steps are printed to the terminal for visibility",
]:
    add_bullet(b)
add_label_value("Output", "[AGENT] 5 steps planned: 1. Define... 2. Provide examples...")

add_sub_heading("Step 3: Step Execution Loop")
for b in [
    "Each step is executed independently with memory context",
    "Every step result is saved to vault with embedding",
]:
    add_bullet(b)
add_label_value("Output", "[STEP 1/5] Define key characteristics -> Supervised learning uses labeled data...")

add_sub_heading("Step 4: Synthesis")
for b in [
    "All step results are passed to a final synthesis call",
    "Summary is saved to vault and evaluated in background",
]:
    add_bullet(b)
add_label_value("Output", "[AGENT COMPLETE] In conclusion, supervised learning maps known inputs to outputs...")

# 7. Memory Pipeline
add_section_heading("7", "Memory Pipeline")

add_sub_heading("Step 1: Query Embedding")
add_bullet("The current user query is embedded using nomic-embed-text via Ollama")
add_bullet("This produces a 768-float vector representing the semantic meaning of the query")

add_sub_heading("Step 2: Cosine Similarity Retrieval")
add_bullet("Every .json file in the vault is scored against the query vector")
add_bullet("Entries are ranked from most to least relevant")

add_sub_heading("Step 3: Context Injection")
add_bullet("The top-5 most relevant entries are selected and formatted")
add_bullet("Hermes receives this context before reasoning - not just the user message")

add_sub_heading("Step 4: Save and Embed Response")
add_bullet("After Hermes responds, save_async() runs in a background thread")
add_bullet("Writes a .md file (readable) and a .json file (embedding vector) - non-blocking")

# 8. Evaluation System
add_section_heading("8", "Self-Evaluation System")
add_body(
    "The system uses two distinct evaluation modes. Chat mode uses a single self-evaluation loop "
    "to track quality over time. Research mode uses a dual evaluation system with opposing personas "
    "to produce a more realistic composite score."
)

add_sub_heading("Chat Evaluation (single-pass)")
add_body(
    "After every chat response, a background thread asks Hermes to evaluate its own output using "
    "EVAL_SYSTEM. The score is stored and used to adapt the system prompt over time."
)
add_simple_table(
    ["Score Range", "Meaning", "System Prompt Action"],
    [
        ["1 - 5",  "Poor quality",    "Add improvement note to next prompt"],
        ["6 - 8",  "Acceptable",      "No change"],
        ["9 - 10", "High quality",    "Add reinforcement note to next prompt"],
    ]
)
add_body(
    "Note: Scores show low variance due to same-model self-evaluation - "
    "a known limitation of single-model feedback loops."
)

add_sub_heading("Research Evaluation (dual-pass - evaluate_approach_dual)")
add_body(
    "Each approach in the research loop is scored by two separate Hermes calls with opposing personas. "
    "The composite score is the average of both, which reduces single-model scoring bias."
)
add_simple_table(
    ["Evaluator", "Persona", "Dimensions Scored", "Bias Direction"],
    [
        ["MULTI_DIM_EVAL_SYSTEM", "Professor", "Strategic quality, Feasibility, Viral potential (each 1-10)", "Positive - finds strengths"],
        ["CRITIC_EVAL_SYSTEM",    "Skeptic",   "Single score - realism and achievability (1-10)",            "Negative - finds weaknesses"],
    ]
)
add_label_value("Professor average", "(strategic + feasibility + viral) / 3")
add_label_value("Composite score",   "(professor average + critic score) / 2")

add_sub_heading("Evaluation Data Stored")
add_simple_table(
    ["Field", "Description"],
    [
        ["score",     "Integer from 1-10 (chat) or composite float (research)"],
        ["reasoning", "One-sentence explanation from Hermes"],
        ["question",  "First 300 characters of the user query"],
        ["response",  "First 300 characters of the Hermes response"],
        ["timestamp", "ISO format datetime"],
    ]
)

# 9. Quality Formula
add_section_heading("9", "Quality Adaptation Formula")

add_sub_heading("Prompt Adaptation Rules")
add_simple_table(
    ["Condition", "Prompt Addition"],
    [
        ["Average < 6.0",         "Your recent responses averaged X/10. Focus on being more thorough and accurate."],
        ["Average >= 8.5",        "Your recent responses averaged X/10. Maintain this standard."],
        ["Fewer than 3 evals",    "No adaptation - baseline still building"],
    ]
)

add_sub_heading("Example Quality Stats Output")
add_label_value("Evaluations", "8")
add_label_value("Average",     "8.2 / 10")
add_label_value("Recent avg",  "9.0 / 10")
add_label_value("Trend",       "improving")

# 10. Data Storage
add_section_heading("10", "Data Storage and Vault Structure")
add_simple_table(
    ["File", "Description"],
    [
        ["*_user.md",          "User messages - readable text with frontmatter"],
        ["*_user.json",        "User message embedding vectors (768 floats)"],
        ["*_hermes.md",        "Hermes responses - readable text with frontmatter"],
        ["*_hermes.json",      "Hermes response embedding vectors"],
        ["*_agent.md",         "Task loop step results"],
        ["*_agent_summary.md", "Task loop final syntheses"],
        ["*_eval.json",        "Quality scores - structured JSON"],
        ["*_system.md",        "Session start markers"],
        ["config.json",        "All runtime configuration"],
    ]
)

# 11. Alignment
add_section_heading("11", "Alignment with Key Concepts")

add_sub_heading("AutoResearch")
add_body("Concept: An AI that can break down a research goal, execute each step, store results, and improve iteratively.")
for b in [
    "The task: command triggers an autonomous research loop",
    "Hermes decomposes the goal into a structured step plan",
    "Each step is executed independently with memory context",
    "A final synthesis call combines all results",
    "The synthesis is evaluated and influences future prompts",
]:
    add_bullet(b)

add_sub_heading("Covenant")
add_body("Concept: Distributed, shared memory across agents - a common knowledge layer.")
for b in [
    "The vault is plain Markdown files - portable and shareable",
    "memory.py is fully decoupled from agent.py",
    "The vault path can be pointed to a shared network location",
    "Multiple Hermes instances reading from the same vault = shared memory",
]:
    add_bullet(b)

add_sub_heading("prima.cpp")
add_body("Concept: Local, efficient execution - keeping inference on-device.")
for b in [
    "Zero cloud dependency - all inference runs on Ollama at localhost",
    "No pip installs - Python standard library only",
    "Background threading prevents saves from blocking the main loop",
    "Graceful fallback if embedding model is unavailable",
]:
    add_bullet(b)

# 12. Tools
add_section_heading("12", "Tools Used in the Workflow")
add_simple_table(
    ["Tool", "Role"],
    [
        ["Ollama",           "Local LLM runtime - serves hermes3 and nomic-embed-text"],
        ["hermes3",          "Reasoning model - answers, plans, evaluates"],
        ["nomic-embed-text", "Embedding model - converts text to 768-float vectors"],
        ["agent.py",         "Orchestration - input loop, task loop, eval threading"],
        ["memory.py",        "Memory layer - embed, save, search, evaluate, summarise"],
        ["config.json",      "All configuration - model, temperature, embed model, prompt"],
        ["Python 3.10+",     "Runtime - standard library only"],
    ]
)

# 13. Setup
add_section_heading("13", "Setup and Prerequisites")

add_sub_heading("What Is Required")
add_simple_table(
    ["Requirement", "Version", "How to Get It"],
    [
        ["Python",           "3.10 or higher", "https://python.org"],
        ["Ollama",           "Latest",          "https://ollama.com"],
        ["hermes3",          "Latest",          "ollama pull hermes3"],
        ["nomic-embed-text", "Latest",          "ollama pull nomic-embed-text"],
    ]
)

add_sub_heading("What Is NOT Required")
for b in ["No API keys", "No paid subscriptions", "No internet after initial download", "No pip install or virtual environment", "No Docker"]:
    add_bullet(b)

add_sub_heading("Startup Steps")
add_label_value("Step 1", "ollama serve")
add_label_value("Step 2", "ollama list  (confirm both models appear)")
add_label_value("Step 3", "cd hermes-rowboat-env")
add_label_value("Step 4", "python agent.py")

add_sub_heading("Potential Blockers and Fixes")
add_simple_table(
    ["Blocker", "Symptom", "Fix"],
    [
        ["Ollama not running",          "Connection refused on first message", "Run ollama serve in a separate terminal"],
        ["hermes3 not pulled",          "model not found error",               "ollama pull hermes3"],
        ["nomic-embed-text not pulled", "No .json files in vault",             "ollama pull nomic-embed-text"],
        ["Python below 3.10",           "Syntax error on startup",             "Upgrade Python to 3.10+"],
    ]
)

# 14. Resources
add_section_heading("14", "Resources")

add_sub_heading("Hardware")
add_simple_table(
    ["Resource", "Minimum", "Recommended"],
    [
        ["RAM",        "8 GB",         "16 GB"],
        ["Disk space", "10 GB free",   "20 GB free"],
        ["GPU",        "Not required", "CUDA GPU for 3-5x speed"],
        ["CPU",        "Any modern",   "8+ core for faster inference"],
    ]
)

add_sub_heading("Software")
add_simple_table(
    ["Tool", "Purpose", "License"],
    [
        ["Python 3.10+",     "Runtime",          "PSF (free)"],
        ["Ollama",           "Local LLM server", "MIT (free)"],
        ["hermes3",          "Reasoning model",  "Llama community (free)"],
        ["nomic-embed-text", "Embedding model",  "Apache 2.0 (free)"],
    ]
)

# 15. Expected Outcome
add_section_heading("15", "Expected Outcome")
for b in [
    "The agent remembers what was discussed in past sessions and retrieves relevant context automatically on every new query.",
    "The agent can receive a high-level goal, decompose it into steps, execute each independently, and synthesise a final answer without human intervention.",
    "Quality scores accumulate over time and the system prompt adapts automatically - the agent improves the more it is used.",
    "No conversation data is ever sent to an external server. The entire pipeline runs on the local machine.",
    "The memory layer is decoupled and can be extended toward shared multi-agent memory in future iterations.",
    "The system demonstrates practical alignment with AutoResearch (task loop), Covenant (portable vault), and prima.cpp (local execution).",
]:
    add_bullet(b)

add_divider()

# ══════════════════════════════════════════════════════════════════════════════
# 16. SCREENSHOTS
# ══════════════════════════════════════════════════════════════════════════════
add_section_heading("16", "Screenshots")

def add_screenshot_placeholder(figure_num, caption, instruction):
    doc.add_paragraph()
    # Placeholder box using a single-cell table
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(5.5)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(40)
    p.paragraph_format.space_after  = Pt(40)
    r = p.add_run(f"[ Insert Screenshot Here ]\n{instruction}")
    set_font(r, size=10)
    r.font.color.rgb = None

    caption_p = doc.add_paragraph()
    caption_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_p.paragraph_format.space_before = Pt(4)
    caption_p.paragraph_format.space_after  = Pt(14)
    cr = caption_p.add_run(f"Figure {figure_num}: {caption}")
    set_font(cr, size=10, bold=True)

add_body(
    "The following screenshots demonstrate the system running locally. "
    "Take each screenshot as described and insert it into the placeholder box above its caption."
)

add_sub_heading("Figure 1 - Agent Running in Terminal")
add_body("How to take: Run python agent.py and send one message. Screenshot the full terminal window.")
add_screenshot_placeholder(
    1,
    "Agent running locally in terminal",
    "python agent.py -> send one message -> screenshot"
)

add_sub_heading("Figure 2 - Memory Command Output with Quality Stats")
add_body("How to take: After 3+ messages, wait 15 seconds, type 'memory'. Screenshot the full output including the QUALITY STATS section.")
add_screenshot_placeholder(
    2,
    "Memory vault contents and quality stats",
    "Type: memory -> screenshot full output"
)

add_sub_heading("Figure 3 - Memory Folder Showing .md and .json Files")
add_body("How to take: Open the memory/ folder in File Explorer or run 'ls memory/' in terminal. Screenshot showing the .md, .json, and _eval.json files.")
add_screenshot_placeholder(
    3,
    "Memory vault folder with .md and .json files",
    "Open memory/ folder -> screenshot file listing"
)

add_sub_heading("Figure 4 - Ollama Model List")
add_body("How to take: Open a terminal and run 'ollama list'. Screenshot showing both hermes3 and nomic-embed-text with their sizes.")
add_screenshot_placeholder(
    4,
    "Ollama model list showing hermes3 and nomic-embed-text",
    "Run: ollama list -> screenshot"
)

add_divider()

# ══════════════════════════════════════════════════════════════════════════════
# 17. AUTORESEARCH EXTENSION
# ══════════════════════════════════════════════════════════════════════════════
add_section_heading("17", "AutoResearch Extension (Implemented)")

add_body(
    "The AutoResearch-inspired research loop is fully implemented via the research: command. "
    "It addresses three specific weaknesses of the original single-pass approach: "
    "same-model evaluation bias, no iteration across rounds, and shallow tie-breaking."
)

add_sub_heading("Three Problems Solved")
add_simple_table(
    ["Problem", "Solution Implemented"],
    [
        ["Evaluation bias (same model)",
         "Dual evaluation: Professor multi-dim + Critic adversarial, averaged into composite score"],
        ["No iteration loop",
         "Multi-round loop: best result from round N seeds 3 refinements in round N+1"],
        ["Shallow selection (ties)",
         "Composite float scoring + head-to-head tiebreaker for scores within 0.5 points"],
    ]
)

add_sub_heading("Research Loop Workflow")
add_workflow(
    "Goal Received (research: <goal>)\n"
    "  -> Round 1: APPROACH_GENERATOR generates 3 distinct approaches (viral / guerrilla / trend-jack)\n"
    "  -> Each approach executed by PROFESSOR_PERSONA with full tactics and platform detail\n"
    "  -> evaluate_approach_dual() runs two Hermes calls per approach:\n"
    "       MULTI_DIM_EVAL_SYSTEM: strategic quality + feasibility + viral potential\n"
    "       CRITIC_EVAL_SYSTEM: realism and achievability (adversarial)\n"
    "       Composite = (professor average + critic score) / 2\n"
    "  -> _select_best() picks highest composite score\n"
    "       Tie (within 0.5 pts): _head_to_head() runs TIEBREAKER_SYSTEM\n"
    "  -> If best composite < quality_threshold (8.0) and iteration < max_iterations (3):\n"
    "       REFINEMENT_GENERATOR produces 3 variations of the best result\n"
    "       (one improves feasibility, one viral potential, one strategic depth)\n"
    "       Loop repeats from execute step with refined approaches\n"
    "  -> Stops when threshold met or max iterations reached\n"
    "  -> Final best result stored in vault with iteration count and composite score"
)

add_sub_heading("New System Prompts Added")
add_simple_table(
    ["Constant", "Role", "Output Format"],
    [
        ["MULTI_DIM_EVAL_SYSTEM",
         "Professor evaluator - 3 dimensions",
         "JSON: strategic_quality, feasibility, viral_potential"],
        ["CRITIC_EVAL_SYSTEM",
         "Skeptical critic - finds weaknesses",
         "JSON: score (harsh), reasoning"],
        ["TIEBREAKER_SYSTEM",
         "Senior strategist - real-world choice",
         "JSON: winner (1 or 2), reasoning"],
        ["REFINEMENT_GENERATOR_SYSTEM",
         "Refinement planner - 3 improved variants (prompt hardened with explicit one-sentence format example)",
         "JSON array of exactly 3 strings"],
    ]
)

add_sub_heading("New Functions Added")
add_simple_table(
    ["Function", "Purpose"],
    [
        ["evaluate_approach_dual(approach, response)",
         "Runs professor + critic evaluations, returns dict with all scores and composite"],
        ["_head_to_head(a, b)",
         "Asks tiebreaker persona to pick between two tied approaches"],
        ["_select_best(results)",
         "Sorts by composite, triggers head-to-head if tie within 0.5 pts"],
        ["run_autoresearch_loop(goal, max_iter, threshold)",
         "Full iterative loop - replaces original single-pass version"],
    ]
)

add_sub_heading("Issues Found During Testing and Fixes Applied")
add_simple_table(
    ["Issue", "Root Cause", "Fix Applied"],
    [
        ["Semantic context bleed",
         "search_relevant() used pure cosine similarity across all vault entries. "
         "Old sessions with similar topics (AI marketing) outranked current session entries (leather wallets).",
         "Hybrid retrieval implemented in memory.py. Current session entries (timestamp >= last system marker) "
         "are always injected first. Past session entries fill remaining slots via cosine similarity. "
         "Current conversation can no longer be crowded out by old similar content."],
        ["Refinement generator returning 6 items instead of 3",
         "Model formatted JSON with both title and description as separate list items, "
         "causing the parser to pick up 6 strings instead of 3.",
         "Prompt hardened with explicit one-sentence format example. "
         "Hard cap approaches[:3] added in agent.py to enforce 3-item limit at code level regardless of model output."],
        ["Same-model evaluation bias (partial)",
         "Professor and critic both use the same Hermes model. Opposing personas reduce variance "
         "but cannot fully eliminate self-assessment bias.",
         "No full fix available without a second independently trained model. "
         "Dual-persona scoring is the best practical mitigation available locally."],
        ["Task loop outputs not stripped of model self-labels",
         "run_task_loop() printed step results and the final synthesis without stripping "
         "[HERMES] or similar labels the model occasionally prefixes to its own output. "
         "Same root cause as the main chat label fix.",
         "re.sub(r'^\\[[A-Z]+\\]\\s*', '', ...) applied to both the step result and synthesis "
         "in run_task_loop() before printing and saving to vault."],
        ["'Saving session and exiting.' misleading quit message",
         "The quit message implied a guaranteed save, but async save threads are daemon threads - "
         "they are killed when the process exits with no flush guarantee.",
         "Message changed to 'Exiting.' to accurately reflect process behaviour."],
        ["'1 approaches' grammar edge case",
         "If JSON parsing of the approach list fails completely and falls back to the raw string, "
         "len(approaches) == 1 and the output would read '1 approaches'.",
         "Singular/plural resolved inline with a conditional expression - 'approach' vs 'approaches' based on count."],
    ]
)

add_sub_heading("Observed Approach Diversity")
add_body(
    "Approach diversity increased between runs - the second execution produced a hashtag challenge, "
    "influencer program, and interactive quiz, distinct from the first run's UGC loop, guerrilla installations, "
    "and trend-jacking - indicating non-repetitive generation behavior."
)
add_body(
    "This enables iterative improvement through stored results and semantic retrieval, "
    "aligned with the AutoResearch concept of accumulating and refining knowledge across cycles."
)

add_divider()

# ══════════════════════════════════════════════════════════════════════════════
# 18. EXPERIMENTAL RESULTS
# ══════════════════════════════════════════════════════════════════════════════
add_section_heading("18", "Experimental Results")
add_body(
    "The following results were observed during live end-to-end testing of the system. "
    "All runs used the default configuration: max_iterations=3, quality_threshold=8.0, "
    "hermes3 via Ollama on a CPU-only machine."
)

add_sub_heading("Test 1 - Research Loop: YouTube Channel Growth")
add_label_value("Goal", "How to grow a YouTube channel to 10,000 subscribers")
add_label_value("Iterations run", "2 out of 3 (threshold met early)")
add_simple_table(
    ["Iteration", "Approach", "Prof avg", "Critic", "Composite", "Selected"],
    [
        ["1", "Viral loop: Subscriber Squad referral challenge",    "7.3", "5.0", "6.2",  ""],
        ["1", "Guerrilla: micro-creator cross-promotion swaps",     "8.0", "7.0", "7.5",  "YES"],
        ["1", "Trend-jack: rapid-response content within 2 hours", "7.7", "6.0", "6.8",  ""],
        ["2", "Refined: feasibility-improved cross-promotion",      "8.3", "7.8", "8.1",  "YES - threshold met"],
    ]
)
add_body(
    "Score trajectory: 7.5 (iteration 1 best) -> 8.1 (iteration 2 best). "
    "The refinement round produced a 0.6-point composite gain. "
    "The quality threshold of 8.0 was met on iteration 2, preventing an unnecessary third round."
)

add_sub_heading("Test 2 - Approach Diversity Across Runs")
add_body(
    "The same goal was submitted in two separate sessions to verify that the approach generator "
    "does not repeat identical strategies."
)
add_simple_table(
    ["Run", "Approach 1", "Approach 2", "Approach 3"],
    [
        ["Run 1", "Viral loop (referral challenge)", "Guerrilla (micro-creator swaps)", "Trend-jacking (rapid-response content)"],
        ["Run 2", "Hashtag challenge (UGC campaign)", "Influencer affiliate program",   "Interactive quiz (engagement bait)"],
    ]
)
add_body(
    "Observation: all six approaches across both runs were distinct. "
    "No strategy was repeated, and the marketing philosophies shifted between runs "
    "(community-building vs performance-driven in run 2 vs run 1). "
    "This confirms non-repetitive generation behavior aligned with the AutoResearch principle "
    "of accumulating and refining knowledge rather than replaying cached answers."
)

add_sub_heading("Test 3 - Context Bleed Fix Verification")
add_body(
    "A two-message sequence was used to verify that the hybrid retrieval fix eliminated context bleed. "
    "Session 1 contained entries about AI marketing strategy. "
    "In a new session, the user asked about leather wallet marketing, then immediately followed up "
    "with 'what are the core materials used in this product?'"
)
add_simple_table(
    ["Condition", "Expected", "Observed"],
    [
        ["Before fix (pure cosine)", "Reference leather wallets",    "Referenced AI marketing (wrong session content)"],
        ["After fix (hybrid)",       "Reference leather wallets",    "Correctly referenced leather and canvas materials"],
    ]
)
add_body(
    "The fix was confirmed working: the in-memory session buffer was injected ahead of vault content, "
    "ensuring the live conversation was never crowded out by semantically similar old entries."
)

add_sub_heading("Key Observations")
for b in [
    "Dual evaluation (professor + critic) consistently produced a realistic score spread - critic scores averaged 1.5-2.0 points below professor averages, indicating the adversarial persona was functioning as intended",
    "No head-to-head tiebreaker was triggered in these tests - composite scores were sufficiently differentiated",
    "Background threading confirmed non-blocking: evaluation results appeared in memory stats 10-15 seconds after the exchange, with no delay to the user's next prompt",
    "Approach parser fallback (nested JSON flattening + hard cap) was triggered once during testing and resolved correctly",
]:
    add_bullet(b)

add_divider()

# Save
doc.save("Hermes + Rowboat_ Self-Improving AI System Plan_v3.docx")
print("Saved: Hermes + Rowboat_ Self-Improving AI System Plan_v3.docx")
