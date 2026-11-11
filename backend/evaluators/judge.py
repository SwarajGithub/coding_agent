import logging
from typing import List, Literal
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from config.settings import get_configured_llm

logger = logging.getLogger("agent.evaluators.judge")


class CodeReviewReport(BaseModel):
    readability_score: int = Field(..., description="Score from 1 to 10 evaluating structure and docstrings.")
    security_vulnerabilities: List[str] = Field(...,
                                                description="List of potential risks, anti-patterns, or gaps found.")
    complexity_rating: Literal["Low", "Medium", "High"] = Field(...,
                                                                description="Estimated algorithmic or cognitive complexity.")
    critique: str = Field(...,
                          description="Constructive engineering feedback regarding formatting or structural optimization.")
    status: Literal["APPROVED", "REJECTED"] = Field(...,
                                                    description="APPROVED if score >= 7 and no critical exploits; REJECTED otherwise.")


def evaluate_code_quality(requirement: str, code_draft: str) -> CodeReviewReport:
    logger.info("Initiating LLM-as-a-judge quality gate verification chain...")

    llm = get_configured_llm(temperature=0.2)

    output_parser = PydanticOutputParser(pydantic_object=CodeReviewReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an unyielding Principal Software Engineer performing a code audit.\n"
                   "Review the provided implementation code against the original specification.\n"
                   "Evaluate documentation, code architecture choices, security flaws, and performance gaps.\n\n"
                   "{format_instructions}"),
        ("human", "### Feature Requirement Spec:\n{requirement}\n\n"
                  "### Implementation Code Under Review:\n```python\n{code_draft}\n```")
    ]).partial(format_instructions=output_parser.get_format_instructions())

    evaluation_chain = prompt | llm | output_parser

    try:
        report = evaluation_chain.invoke({
            "requirement": requirement,
            "code_draft": code_draft
        })
        logger.info(f"Quality gate complete. Status: {report.status} | Score: {report.readability_score}/10")
        return report

    except Exception as eval_err:
        logger.error(f"Failed to generate structured judge report: {str(eval_err)}")
        # Provide a graceful fallback schema block if parsing fails
        return CodeReviewReport(
            readability_score=5,
            security_vulnerabilities=["Failed to parse evaluation report metrics cleanly."],
            complexity_rating="Medium",
            critique=f"Internal evaluation processor parsing anomaly: {str(eval_err)}",
            status="REJECTED"
        )
