from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class LLMConfig:
    backend: str = os.getenv("LLM_BACKEND", "mock")
    model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    openai_compat_url: str = os.getenv(
        "OPENAI_COMPAT_URL", "https://api.openai.com/v1/chat/completions"
    )
    api_key: Optional[str] = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))


class LLMClient:
    """Small wrapper supporting a mock backend, Ollama, or an OpenAI-compatible endpoint."""

    def __init__(self, config: Optional[LLMConfig] = None) -> None:
        self.config = config or LLMConfig()

    @property
    def backend(self) -> str:
        return self.config.backend

    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        backend = self.config.backend.lower().strip()
        if backend == "mock":
            return self._mock_generate(system_prompt, user_prompt)
        if backend == "ollama":
            return self._ollama_generate(system_prompt, user_prompt, temperature)
        if backend in {"openai", "openai_compat", "compatible"}:
            return self._openai_compat_generate(system_prompt, user_prompt, temperature)
        raise ValueError(f"Unsupported LLM_BACKEND: {self.config.backend}")

    def _ollama_generate(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }
        response = requests.post(
            self.config.ollama_url,
            json=payload,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"].strip()

    def _openai_compat_generate(
        self, system_prompt: str, user_prompt: str, temperature: float
    ) -> str:
        if not self.config.api_key:
            raise ValueError("OPENAI_API_KEY or LLM_API_KEY is required for openai_compat mode.")

        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self.config.openai_compat_url,
            headers=headers,
            json=payload,
            timeout=self.config.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _mock_generate(self, system_prompt: str, user_prompt: str) -> str:
        lines = [line.strip() for line in user_prompt.splitlines() if line.strip()]
        query_line = next((line for line in lines if line.lower().startswith("user question:")), "")
        query = query_line.split(":", 1)[1].strip().lower() if ":" in query_line else ""
        sources = [line for line in lines if line.startswith("[")]
        source_ids = []
        for line in sources[:5]:
            chunk_id = line.split("]", 1)[0].lstrip("[")
            source_ids.append(chunk_id)

        specialized = "Action Plan:" in system_prompt and "Safety Note:" in system_prompt
        citations = " ".join(f"[{source_id}]" for source_id in source_ids[:3]) if source_ids else ""

        if "conflict" in query:
            summary = "There is an exact-time conflict around 18:00 in the saved schedule."
            actions = [
                "Compare the pets with 18:00 tasks and decide whether one task should move.",
                "Keep high-priority recurring items visible first.",
            ]
        elif "luna" in query or "milo" in query or "today" in query:
            summary = "Luna and Milo both have saved routine tasks that should be reviewed for today."
            actions = [
                "Complete Luna's scheduled walk or medication reminders on time.",
                "Complete Milo's feeding or grooming tasks that appear in the schedule.",
                "Check for any same-time collisions before the day starts.",
            ]
        else:
            summary = "Here is a grounded care summary based on the retrieved schedule and care notes."
            actions = [
                "Review the highest-priority scheduled tasks first.",
                "Resolve any exact-time conflicts before the day starts.",
                "Keep recurring feeding, walk, or medication reminders on time.",
            ]

        if not specialized:
            return f"{summary} {citations}".strip()

        return (
            "Summary:\n"
            f"{summary}\n\n"
            "Action Plan:\n"
            + "\n".join(f"- {item}" for item in actions)
            + "\n\nWhy:\n"
            + f"- The retrieved context points to scheduled care responsibilities and routine guidance. {citations}\n\n"
            + "Sources:\n"
            + "\n".join(f"- [{source_id}]" for source_id in source_ids)
            + "\n\nSafety Note:\n"
            + "This planner is for routine organization only and does not diagnose illness or give medication dosages."
        ).strip()