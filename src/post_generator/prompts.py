"""Prompt templates and the shared system preamble.

Every generative prompt inherits SYSTEM_PREAMBLE, which enforces the core principles:
be logical, use only real facts, do not hallucinate, and keep creativity at a medium level.
"""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

SYSTEM_PREAMBLE = (
    "You are a precise assistant. Be logical and rely only on the provided facts and the topic. "
    "Do not invent facts, statistics, names, or events. If you are unsure, stay general rather "
    "than fabricate. Creativity level: medium."
)

# --- Sufficiency judge -------------------------------------------------------
SUFFICIENCY_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PREAMBLE),
        (
            "human",
            "Decide whether the CONTENT below is sufficient and relevant to write a grounded, "
            "factual LinkedIn post about the TOPIC. It is sufficient only if it contains concrete, "
            "on-topic information (not just a passing mention).\n\n"
            "TOPIC:\n{topic}\n\nCONTENT:\n{content}\n\n"
            "Answer with the structured verdict.",
        ),
    ]
)

# --- Search agent ------------------------------------------------------------
# create_agent (LangChain 1.x) takes a plain system-prompt string.
SEARCH_SYSTEM_PROMPT = (
    SYSTEM_PREAMBLE
    + "\n\nYou are a research assistant. Use the duckduckgo_search tool to gather current, "
    "factual information about the topic. Perform one or more searches, then write a concise, "
    "well-organized factual summary (5-10 sentences) that could ground a LinkedIn post. Only "
    "state facts you found; do not speculate. Cite nothing inline -- just summarize."
)

# --- Content generator -------------------------------------------------------
CONTENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PREAMBLE),
        (
            "human",
            "Write a LinkedIn post about the TOPIC, grounded strictly in the CONTENT.\n"
            "Requirements:\n"
            "- Start with a strong one-line hook.\n"
            "- 2-4 short paragraphs, professional but human tone.\n"
            "- End with an optional light call-to-action.\n"
            "- Add 3-5 relevant hashtags on the last line.\n"
            "- Do not invent facts beyond the CONTENT. Output only the post text.\n\n"
            "TOPIC:\n{topic}\n\nCONTENT:\n{content}",
        ),
    ]
)

# --- Image prompt generator --------------------------------------------------
IMAGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PREAMBLE),
        (
            "human",
            "Create a single detailed prompt for an image-generation model to illustrate a "
            "LinkedIn post about the TOPIC (grounded in the CONTENT).\n"
            "Describe: main subject, setting, style (e.g. clean modern flat illustration or "
            "professional photograph), color mood, and composition. Keep it literal and concrete. "
            "Do NOT include any text, words, letters, or logos in the image. "
            "Output only the image prompt, one paragraph, no preamble.\n\n"
            "TOPIC:\n{topic}\n\nCONTENT:\n{content}",
        ),
    ]
)
