import os
import json
import logging
from typing import List, Dict, Any, Optional

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def save_markdown(self, original_path: str, content: str) -> Optional[str]:
        try:
            base = os.path.splitext(original_path)[0]
            new_path = f"{base}_rewritten.md"

            with open(new_path, "w", encoding="utf-8") as f:
                f.write(content)

            return new_path
        except Exception as e:
            logger.error(f"❌ Save error: {e}")
            return None


# ===============================
# LLM
# ===============================

def get_llm(temp=0.3):
    return ChatOpenAI(
        model=os.getenv("OPEN_ROUTER_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPEN_ROUTER_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temp,
        max_retries=2
    )


# ===============================
# DATA MODEL
# ===============================

class QualityScore(BaseModel):
    structure_score: int
    coverage_score: int
    examples_score: int
    clarity_score: int
    formatting_score: int
    final_score: float
    missing: List[str]
    feedback: str


# ===============================
# 1. EVALUATOR AGENT
# ===============================

class EvaluatorAgent:

    def __init__(self):
        self.llm = get_llm(0.2)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert evaluator. Return ONLY JSON."),
            ("human",
             """
Evaluate notes:

1. Structure
2. Coverage
3. Examples
4. Clarity
5. Formatting

NOTES:
{notes}

Return JSON:
{
 "structure_score": 0-100,
 "coverage_score": 0-100,
 "examples_score": 0-100,
 "clarity_score": 0-100,
 "formatting_score": 0-100,
 "final_score": float,
 "missing": [],
 "feedback": ""
}
""")
        ])

        self.chain = self.prompt | self.llm | JsonOutputParser()

    def run(self, notes: str) -> Dict[str, Any]:
        return self.chain.invoke({"notes": notes})


# ===============================
# 2. WRITER AGENT
# ===============================

class WriterAgent:

    def __init__(self):
        self.llm = get_llm(0.7)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert educator. Improve notes quality in Markdown."),
            ("human",
             """
Rewrite these notes to improve quality:

- Fix structure
- Add clarity
- Add examples
- Improve formatting

NOTES:
{notes}

FEEDBACK:
{feedback}
""")
        ])

        self.chain = self.prompt | self.llm

    def run(self, notes: str, feedback: str) -> str:
        return self.chain.invoke({
            "notes": notes,
            "feedback": feedback
        })


# ===============================
# 3. REVIEWER AGENT
# ===============================

class ReviewerAgent:

    def __init__(self):
        self.llm = get_llm(0.2)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a strict reviewer. Return ONLY JSON."),
            ("human",
             """
Final review:

Is this notes quality acceptable?

Return:
{
 "approved": true/false,
 "reason": ""
}

NOTES:
{notes}
""")
        ])

        self.chain = self.prompt | self.llm | JsonOutputParser()

    def run(self, notes: str) -> Dict[str, Any]:
        return self.chain.invoke({"notes": notes})


# ===============================
# ORCHESTRATOR (BRAIN CONTROLLER)
# ===============================

class NoteQualityOrchestrator:

    THRESHOLD = 70
    MAX_ITERATIONS = 3

    def __init__(self):
        self.evaluator = EvaluatorAgent()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()

    def run(self, notes: str):

        logger.info("🚀 Multi-Agent System Started")

        current_text = notes
        history = []
        attempt = 0

        for i in range(self.MAX_ITERATIONS):

            # 1. Evaluate
            evaluation = self.evaluator.run(current_text)
            history.append({"step": "evaluate", "result_set": evaluation, "attempt": attempt})

            score = evaluation["final_score"]
            feedback = evaluation["feedback"]

            logger.info(f"📊 Iteration {i+1} Score: {score}")

            # 2. Check condition
            if score >= self.THRESHOLD:
                break

            # 3. Rewrite
            current_text = self.writer.run(current_text, feedback)
            attempt+=1
            history.append({"step": "rewrite", "text": current_text})

        # 4. Final Review
        review = self.reviewer.run(current_text)

        return {
            "final_text": current_text,
            "final_score": score,
            "review": review,
            "history": history,
            "attempts": attempt
        }


# ===============================
# ENTRY FUNCTION
# ===============================

def NoteQualityCheck(file_path : str ,raw_text: str):
    THRESHOLD = 70
    system = NoteQualityOrchestrator()
    final_text,final_score,review,history = system.run(raw_text)
    
    if final_score >= THRESHOLD:
            new_path = save_markdown(file_path, final_text)
            return new_path if new_path else file_path

    return file_path
