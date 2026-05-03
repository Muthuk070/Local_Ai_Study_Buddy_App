import os
import json
import logging
from typing import List, Dict, Type, Any
import json
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.tools import BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_markeddown(file_path: str, content: str) -> Optional[str]:
    try:
        base, _ = os.path.splitext(file_path)
        new_path = f"{base}_improved.md"
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(content)
        return new_path
    except Exception as e:
        logger.error(f"Error saving improved notes: {e}")
        return None


# =========================================================
# LLM
# =========================================================

def get_llm(temp:float = 0.0) -> ChatOpenAI:
  # configurable timeout and retries via env
  timeout = float(os.getenv("OPEN_ROUTER_TIMEOUT", "30"))
  max_retries = int(os.getenv("OPEN_ROUTER_MAX_RETRIES", "3"))

  params = {
    "model": os.getenv("OPEN_ROUTER_MODEL", "gpt-4o-mini"),
    "openai_api_key": os.getenv("OPEN_ROUTER_KEY"),
    "openai_api_base": os.getenv("OPEN_ROUTER_BASE", "https://openrouter.ai/api/v1"),
    "temperature": temp,
    # try common timeout/retry keys; some langchain/openai wrappers accept these
    "request_timeout": timeout,
    "timeout": timeout,
    "max_retries": max_retries,
  }

  # Some ChatOpenAI implementations may not accept all kwargs; try progressively
  try:
    return ChatOpenAI(**params)
  except TypeError:
    # remove optional keys and retry
    for key in ("request_timeout", "timeout", "max_retries"):
      params.pop(key, None)
    try:
      return ChatOpenAI(**params)
    except TypeError:
      # last resort: pass only essential args
      essential = {k: params[k] for k in ("model", "openai_api_key", "openai_api_base", "temperature")}
      return ChatOpenAI(**essential)



# =========================================================
# TOOL 1: EVALUATOR
# =========================================================

class EvaluateNotesTool(BaseTool):
    name: str = "evaluate_notes"
    description: str = (
        "Evaluate notes quality and return JSON scores. "
        "Use this first to assess quality."
    )

    def _run(self, notes: str) -> str:
        llm = get_llm(0.0)

        prompt = ChatPromptTemplate.from_messages([
            """ "system":
You are a STRICT and highly critical educational content evaluator.

Your task is to evaluate educational notes and assign scores (0–100) for each category based on the rules below.

Be harsh, analytical, and unbiased. Do NOT be lenient. Only give high scores if the content clearly meets high standards.


CRITICAL EVALUATION PROCESS (MANDATORY):
1. Identify ALL issues in the content
2. Classify each issue as below two levels:
   - MAJOR issue: breaks understanding, flow missing, in-complete, missing context, incomplete explanation
   - MINOR issue: formatting or small clarity issues

EVALUATION CATEGORIES (0–100 each):

1. Structure (structure_score):
- Clear headings and sections
- Logical flow from main topic to subtopics
- Proper organization and sequencing

2. Coverage (coverage_score):
- All key aspects of the topic are covered
- Sufficient depth of explanation
- Complex topics explained as in clean and simple way
- No missing important subtopics

3. Examples (examples_score):
- Presence of relevant or real-world examples
- Examples improve understanding
- Accuracy and relevance of examples

4. Clarity (clarity_score):
- Simple and understandable language
- No broken or incomplete sentences/words
- No break or unfinished thoughts or unrelated content inbetween lines
- No missing context between lines
- Jargon is explained

5. Formatting (formatting_score):
- spacing, alignment formatting should be consistent
- Clean and readable layout
- structured properly

NOTES TO EVALUATE:
---
{notes}
---

STRICT PENALTY RULES (APPLY PER ISSUE):

- Missing context / broken meaning:
  → Reduce clarity_score by 20–30

- Irrelevant content:
  → Reduce coverage_score by 20–35

- Broken logical flow:
  → Reduce structure_score by 25–40

- Incomplete explanations:
  → Reduce clarity_score AND coverage_score by 20–30

- Poor formatting:
  → Reduce formatting_score by 20–25

- No examples:
  → Reduce examples_score by 20+


FINAL SCORE RULES (STRICT):

Step 1: Calculate average:
final_score = (structure + coverage + examples + clarity + formatting) / 5

Step 2: Use average ONLY IF:
- ALL category scores ≥ 70

Step 3: If ANY category < 70:
- DO NOT use average
- final_score MUST be < 69

Step 4: Bottleneck rule:
- final_score MUST be controlled by the lowest score

Step 5: Very low condition:
- If any category < 60:
  → final_score ≈ (lowest score + 5 to 10)
  → Usually should NOT exceed 65

Example:
structure = 50, others = 75–80
→ average ≈ 71 (IGNORE)
→ final_score ≈ 60–65


CORE RULE:
- ALL ≥ 70 → use average for final_score
- ANY < 70 → NO average for final_score, MUST be < 69
  - Lowest score controls final_score


MISSING FIELD RULE:

Generate "missing" ONLY if any category < 70.

Score-based detail level:

1. ≤ 45:
- List ALL major issues with detailed bulleting points
- Be specific (topics, sections, exact problems)

2. 46–65:
- You should meantion Few bullet points only
- Mention key issues as in minor identification of issues (short phrases)

3. 66–69:
- you should mention 1–3 issues alone as in bullet points 
- Only high-impact gaps alone (e.g., one major issue or 2 minor issues)

Rules:
- No generic statements
- No repetition
- Only actual issues from notes
- Do NOT fabricate issues; only identify real problems in the content
- Mention exactly from which category the issue is falls under and what exactly is missing from the notes in that category)


FEEDBACK RULE:

If final_score < 70:
→ 3–4 lines summarizing major issues and improvements

If final_score ≥ 70:
→ 3–4 lines summarizing strengths

Return ONLY JSON:
{{
 "structure_score": 0-100,
 "coverage_score": 0-100,
 "examples_score": 0-100,
 "clarity_score": 0-100,
 "formatting_score": 0-100,
 "final_score": float,
 "missing": [],
 "feedback": ""
}}
"""])
        

        chain = prompt | llm | JsonOutputParser()

        result = chain.invoke({"notes": notes})
        return json.dumps(result)


# =========================================================
# TOOL 2: REWRITER
# =========================================================

class RewriteNotesTool(BaseTool):
    name: str = "rewrite_notes"
    description: str = (
        "Rewrite notes to improve quality using evaluator feedback."
    )

    def _run(self, notes: str, feedback: str) -> str:
        llm = get_llm(0.2)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert educator. Improve notes into high-quality Markdown."),
            ("human",
             """
Rewrite these notes:

ISSUES:
{feedback}

NOTES:
{notes}

NOTE: Address ALL issues mentioned in the feedback. Do NOT skip any point. Make sure to improve structure, coverage, clarity, examples, and formatting as needed.

Return ONLY improved notes in Markdown with proper formatting.
""")
        ])

        chain = prompt | llm

        return chain.invoke({
            "notes": notes,
            "feedback": feedback
        }).content


# =========================================================
# TOOL 3: REVIEWER (FINAL GUARD)
# =========================================================

class ReviewNotesTool(BaseTool):
    name: str = "review_notes"
    description: str = (
        "Final validation tool. Checks if notes are acceptable."
    )

    def _run(self, notes: str) -> str:
        llm = get_llm(0.2)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a strict reviewer. Return ONLY JSON."),
            ("human",
             """
Final check:

Return:
{{
 "approved": true/false,
 "reason": ""
}}

NOTES:
{notes}
""")
        ])

        chain = prompt | llm | JsonOutputParser()   # This is NOT executed yet , it an piepline, the pripline conatins  prompt and llm and then parse output as json

        result = chain.invoke({"notes": notes})
        return json.dumps(result)


# =========================================================
# PARTIAL CONTROLLED AGENT (MANUAL CONTROL)
# =========================================================

class NoteQualityAgent():
    

    def __init__(self):
        self.count =0
        

    def run(self, notes: str):
        evaluator = EvaluateNotesTool()
        rewriter = RewriteNotesTool()

        # Step 1: Evaluate
        print("Evaluating initial notes...")
        eval_result = json.loads(evaluator._run(notes))
        print("Initial Eval:", eval_result) #return the json result fully
        print()

        score = eval_result.get("final_score", 0)
        feedback = eval_result.get("feedback", "None")

        best_notes = notes

        # Step 2: Improve loop
        for i in range(3):
            if score >= 70:
                break

            improved = rewriter._run(best_notes, feedback)

            if hasattr(improved, "content"):
                improved = improved.content

            best_notes = improved

            eval_result = json.loads(evaluator._run(best_notes))
            print("Re-written Eval:", eval_result)
            self.count+=1
            print()
            score = eval_result.get("final_score", 0)
            feedback = eval_result.get("feedback", "None")


        return {
            "improved_notes": best_notes,
            "final_score": score,
            "feedback": feedback,
            "iterations": self.count
        }    



# =========================================================
# ENTRY FUNCTION (USED IN YOUR FASTAPI)
# =========================================================

def NoteQualityCheck(file_path: str, raw_text: str):
    agent = NoteQualityAgent()
    X = agent.run(raw_text)
    print("Final Improved Notes details;")
    print("Improved Notes:",X["improved_notes"][:1000])
    print("Final Score:", X["final_score"])
    print("Feedback:", X["feedback"])
    print("Total Iterations for re_written:", X["iterations"])
    
    if X["iterations"] > 0: 
        newpath = save_markeddown(file_path, X["improved_notes"])
        return newpath if newpath else 0
    return 0  # No improvement needed, return original path or indicator
    






page_wise_figures = {
    "4": [
      "FIGURE 14.1",
      "FIGURE 14.2(a)",
      "FIGURE 14.2(b)",
      "FIGURE 14.2(c)"
    ],
    "5": [
      "FIGURE 14.3"
    ],
    "6": [
      "FIGURE 14.4",
      "FIGURE 14.5(a)",
      "FIGURE 14.5(b)"
    ],
    "7": [
      "FIGURE 14.6(a)",
      "FIGURE 14.6(b)"
    ],
    "8": [
      "FIGURE 14.7(a)",
      "FIGURE 14.7(b)"
    ],
    "9": [
      "FIGURE 14.8(a)",
      "FIGURE 14.8(b)"
    ],
    "10": [
      "FIGURE 14.9(a)",
      "FIGURE 14.9(b)"
    ],
    "11": [
      "FIGURE 14.10"
    ],
    "12": [
      "FIGURE 14.11(a)",
      "FIGURE 14.11(b)",
      "FIGURE 14.12(a)",
      "FIGURE 14.12(b)"
    ],
    "13": [
      "FIGURE 14.13(a)",
      "FIGURE 14.13(b)",
      "FIGURE 14.14"
    ],
    "14": [
      "FIGURE 14.15(a)",
      "FIGURE 14.15(b)",
      "FIGURE 14.16"
    ],
    "15": [
      "FIGURE 14.17"
    ],
    "16": [
      "FIGURE 14.18"
    ],
    "17": [
      "FIGURE 14.19"
    ],
    "18": [
      "FIGURE 14.20"
    ]
  }












# simple workflow

# User → invoke()
#       ↓
# Executor starts loop (main engine starts)
#       ↓
# LLM thinks → choose tool
#       ↓
# Tool executes (_run)
#       ↓
# Result → back to LLM(→ Stores result in scratchpad (memory)- main engine memory)
#       ↓
# So Now the Main engine LLM decides next step? what to do? -> if score >=70 → stop, else rewrite
#       ↓
# Repeat
#       ↓
# Stop (until review_notes approves OR score is good (For notes quality the score should be above >=70, so then only you should stop))











# invoke()               result = self.executor.invoke({ "input": f"""Improve these notes until they are high quality:NOTES:{notes}"""})return result
#    ↓
# 🧠 LLM chooses tool
#    ↓
# ⚙️ That tool's _run() executes
#    ↓
# 📥 Result goes back to LLM (→ Stores result in scratchpad (memory)- main engine memory - AgentExecutor)
#    ↓
# 🔁 Repeat (if needed accodingly)





















# AgentExecutor
#     ↓
# Agent selects tool
#     ↓
# Tool._run()
#     ↓
# Prompt created   
#     ↓
# chain = prompt | llm
#     ↓
# invoke()
#     ↓
# Fill variables
#     ↓
# Send prompt to LLM
#     ↓
# LLM response
#     ↓
# Return result to AgentExecutor





