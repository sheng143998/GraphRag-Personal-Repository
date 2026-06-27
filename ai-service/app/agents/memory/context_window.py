from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContextWindowConfig:
    max_tokens: int = 8192
    light_compress_threshold: float = 0.60
    aggressive_compress_threshold: float = 0.80
    recent_turns_keep: int = 3
    summary_max_chars: int = 200


@dataclass
class ContextMessage:
    role: str
    content: str
    token_count: int = 0
    turn_index: int = 0


@dataclass
class CurrentTask:
    task_id: str = ""
    phase: str = "idle"
    phase_step: str = ""
    total_steps: int = 0
    completed_steps: list[str] = field(default_factory=list)
    next_step: str = ""
    goal: str = ""
    constraints: list[str] = field(default_factory=list)

    def to_prompt_section(self) -> str:
        """Render current_task as a structured prompt section."""
        if not self.task_id:
            return ""
        completed = ", ".join(self.completed_steps) if self.completed_steps else "(none)"
        constraints_str = ", ".join(self.constraints) if self.constraints else "(none)"
        return (
            f"[TASK STATE]\n"
            f"  Task: {self.task_id}\n"
            f"  Phase: {self.phase} (step {self.phase_step}, {len(self.completed_steps)}/{self.total_steps} done)\n"
            f"  Completed: {completed}\n"
            f"  Next: {self.next_step}\n"
            f"  Goal: {self.goal}\n"
            f"  Constraints: {constraints_str}\n"
        )


class ContextWindowManager:
    """Layer 1: LLM context window management with token buffer and compression.

    Manages the LLM context window by tracking token usage and triggering
    compression when thresholds are exceeded. Maintains a structured
    current_task field so the LLM always knows where it is in a multi-step
    workflow.
    """

    def __init__(self, config: ContextWindowConfig | None = None) -> None:
        self.config = config or ContextWindowConfig()
        self._messages: list[ContextMessage] = []
        self._current_task = CurrentTask()
        self._summary: str = ""
        self._turn_counter: int = 0

    # ------------------------------------------------------------------
    # Message management
    # ------------------------------------------------------------------

    def add_message(self, role: str, content: str, token_count: int | None = None) -> None:
        tokens = token_count or self._estimate_tokens(content)
        self._messages.append(
            ContextMessage(
                role=role,
                content=content,
                token_count=tokens,
                turn_index=self._turn_counter,
            )
        )

    def add_turn(self, user_content: str, assistant_content: str) -> None:
        self.add_message("user", user_content)
        self.add_message("assistant", assistant_content)
        self._turn_counter += 1

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    @property
    def total_tokens(self) -> int:
        return sum(msg.token_count for msg in self._messages)

    @property
    def usage_ratio(self) -> float:
        if self.config.max_tokens <= 0:
            return 0.0
        return self.total_tokens / self.config.max_tokens

    def needs_light_compression(self) -> bool:
        return self.usage_ratio >= self.config.light_compress_threshold

    def needs_aggressive_compression(self) -> bool:
        return self.usage_ratio >= self.config.aggressive_compress_threshold

    # ------------------------------------------------------------------
    # Compression
    # ------------------------------------------------------------------

    def compress(self) -> str | None:
        """Apply compression based on current usage ratio.

        Returns a summary string if compression was applied, None otherwise.
        """
        if not self.needs_light_compression():
            return None

        if self.needs_aggressive_compression():
            return self._aggressive_compress()
        return self._light_compress()

    def create_compression_prompt(self) -> str:
        """Build the prompt for LLM-based summary compression."""
        old_turns = [
            msg for msg in self._messages
            if msg.turn_index < self._turn_counter - self.config.recent_turns_keep
        ]
        if not old_turns:
            return ""
        conversation = "\n".join(
            f"[{msg.role}]: {msg.content[:300]}" for msg in old_turns
        )
        return (
            "Summarize the following conversation history in one or two sentences "
            "in Chinese. Keep all key facts: mentioned products, versions, error "
            "codes, symptoms, and any partial conclusions.\n\n"
            f"{conversation}\n\n"
            "Summary:"
        )

    def _light_compress(self) -> str:
        summary_prompt = self.create_compression_prompt()
        if not summary_prompt:
            return ""
        self._summary = (
            f"[Context Summary] {summary_prompt[:self.config.summary_max_chars]}"
        )
        return self._summary

    def _aggressive_compress(self) -> str:
        self._light_compress()
        keep_count = self.config.recent_turns_keep * 2  # user + assistant per turn
        if len(self._messages) > keep_count:
            self._messages = self._messages[-keep_count:]
        return self._summary

    # ------------------------------------------------------------------
    # Current task
    # ------------------------------------------------------------------

    @property
    def current_task(self) -> CurrentTask:
        return self._current_task

    def update_task(
        self,
        *,
        task_id: str | None = None,
        phase: str | None = None,
        phase_step: str | None = None,
        total_steps: int | None = None,
        next_step: str | None = None,
        goal: str | None = None,
        constraints: list[str] | None = None,
    ) -> None:
        if task_id is not None:
            self._current_task.task_id = task_id
        if phase is not None:
            self._current_task.phase = phase
        if phase_step is not None:
            if phase_step not in self._current_task.completed_steps:
                old_step = self._current_task.phase_step
                if old_step:
                    self._current_task.completed_steps.append(old_step)
            self._current_task.phase_step = phase_step
        if total_steps is not None:
            self._current_task.total_steps = total_steps
        if next_step is not None:
            self._current_task.next_step = next_step
        if goal is not None:
            self._current_task.goal = goal
        if constraints is not None:
            self._current_task.constraints = list(constraints)

    def mark_step_completed(self, step_name: str) -> None:
        if step_name not in self._current_task.completed_steps:
            self._current_task.completed_steps.append(step_name)

    # ------------------------------------------------------------------
    # Build final context for LLM
    # ------------------------------------------------------------------

    def build_context_messages(self, system_prompt: str) -> list[dict[str, str]]:
        """Build the complete message list for sending to the LLM."""
        messages: list[dict[str, str]] = []

        # 1. System prompt (includes current_task)
        task_section = self._current_task.to_prompt_section()
        full_system = system_prompt
        if task_section:
            full_system = task_section + "\n" + system_prompt
        messages.append({"role": "system", "content": full_system})

        # 2. Compressed summary (if any)
        if self._summary:
            messages.append({
                "role": "system",
                "content": f"[Compressed History] {self._summary}",
            })

        # 3. Recent messages
        for msg in self._messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def build_prompt_text(self, system_prompt: str) -> str:
        """Build a flat prompt string (for simple LLM adapters)."""
        parts: list[str] = []

        task_section = self._current_task.to_prompt_section()
        if task_section:
            parts.append(task_section)
        parts.append(system_prompt)

        if self._summary:
            parts.append(f"[Compressed History] {self._summary}")

        for msg in self._messages:
            parts.append(f"{msg.role}: {msg.content}")

        return "\n\n".join(parts)

    def reset(self) -> None:
        self._messages.clear()
        self._current_task = CurrentTask()
        self._summary = ""
        self._turn_counter = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        chars = len(text)
        words = len(text.split())
        return max(1, (chars + words * 4) // 4)

    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def turn_count(self) -> int:
        return self._turn_counter
