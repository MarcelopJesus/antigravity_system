"""BaseAgent — Abstract base class for all pipeline agents."""
import time
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentResult:
    """Result from an agent execution."""
    content: object
    duration_ms: float
    agent_name: str
    success: bool
    input_chars: int = 0
    output_chars: int = 0
    error: str = ""


class BaseAgent(ABC):
    """Abstract base class for pipeline agents."""

    name: str = "base"

    def __init__(self, llm_client, knowledge_base=None):
        self.llm = llm_client
        self.kb = knowledge_base

    @abstractmethod
    def _build_prompt(self, input_data) -> str:
        """Build the prompt for this agent. Must be implemented by subclasses."""
        ...

    @abstractmethod
    def _parse_response(self, raw_text: str, input_data=None) -> object:
        """Parse the raw LLM response. Must be implemented by subclasses."""
        ...

    def _get_json_mode(self) -> bool:
        """Override to True for agents that need JSON responses."""
        return False

    def _get_kb_filter(self):
        """Override to specify which KB files to load. None means no KB needed."""
        return None

    def _load_kb(self):
        """Loads knowledge base content filtered for this agent."""
        if self.kb is None:
            return ""
        kb_filter = self._get_kb_filter()
        if kb_filter is None:
            return ""
        return self.kb.load(file_filter=kb_filter)

    def validate_output(self, result) -> bool:
        """Override to add output validation. Returns True by default."""
        return True

    def execute(self, input_data) -> AgentResult:
        """Execute the agent: build prompt, call LLM, parse response, return result."""
        input_chars = len(str(input_data))
        start = time.time()

        try:
            prompt = self._build_prompt(input_data)
            raw_text = self.llm.generate(prompt, json_mode=self._get_json_mode())
            content = self._parse_response(raw_text, input_data)
            duration_ms = (time.time() - start) * 1000

            output_chars = len(str(content))
            logger.info(
                "[%s] completed in %.0fms (input=%d chars, output=%d chars)",
                self.name, duration_ms, input_chars, output_chars
            )

            return AgentResult(
                content=content,
                duration_ms=duration_ms,
                agent_name=self.name,
                success=True,
                input_chars=input_chars,
                output_chars=output_chars,
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            logger.error("[%s] failed after %.0fms: %s", self.name, duration_ms, e)
            return AgentResult(
                content=None,
                duration_ms=duration_ms,
                agent_name=self.name,
                success=False,
                input_chars=input_chars,
                error=str(e),
            )

    @staticmethod
    def clean_llm_output(text: str) -> str:
        """Removes markdown code block wrappers from LLM output."""
        clean = re.sub(r"^```html\s*", "", text, flags=re.IGNORECASE)
        clean = re.sub(r"^```\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"```$", "", clean, flags=re.IGNORECASE)
        return clean.strip()
