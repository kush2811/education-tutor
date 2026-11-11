"""Context management service: preserves relevant conversation history for follow-ups while isolating sessions."""

import re
from typing import List, Tuple, Optional, Dict
from sqlalchemy.orm import Session

from app.models.session import StudySession, SessionMessage


# Pronouns, ellipses, and short follow-up requests indicating reliance on prior session context
ANAPHORIC_PATTERNS = [
    r'\b(that|it|this|these|those|their|them|the above|previous|earlier)\b',
    r'\b(why|how come|what about|how about|what if)\b',
    r'\b(step\s*\d+|formula|equation|result|solution|code|program|table|line by line)\b',
    r'\b(repeat|continue|elaborate|simplify|clarify|explain more|example|examples|practice|quiz)\b',
    r'^\s*(more|details|why\??|how\??|example\??|give code|truth tables?)\s*$'
]


class ConversationContextManager:
    """Manages dialogue state and anaphoric resolution within isolated study sessions."""

    def is_follow_up_inquiry(self, query: str) -> bool:
        """Detect whether student question relies on context from earlier messages."""
        q_lower = query.lower().strip()
        if len(q_lower.split()) <= 4 and any(
            w in q_lower for w in ("example", "why", "code", "more", "explain", "practice", "table", "line")
        ):
            return True
        return any(re.search(pat, q_lower) for pat in ANAPHORIC_PATTERNS)

    def extract_relevant_context(
        self,
        session_id: Optional[str],
        current_query: str,
        db: Session,
        max_turns: int = 10,
        user_id: Optional[str] = None,
        student_id: Optional[str] = None,
        max_total_chars: int = 24000,
    ) -> Tuple[List[Dict[str, str]], bool, Optional[str]]:
        """
        Retrieve relevant prior dialogue history strictly bounded within session_id and owner.

        Returns:
            - List of formatted turn dicts in chronological order [{'role': 'user'|'assistant', 'content': '...'}]
            - is_follow_up (bool)
            - relevant_summary (Optional[str])
        """
        if not session_id:
            # New or unattached inquiry - strict zero context bleed
            return [], False, None

        session = db.query(StudySession).filter(StudySession.id == session_id).first()
        if not session:
            return [], False, None

        # Enforce strict session ownership isolation so users never see another user's context
        if session.user_id is not None:
            if user_id is not None and session.user_id != user_id:
                raise PermissionError("Access denied: session belongs to another user.")
        elif student_id is not None and session.student_id and session.student_id != student_id:
            raise PermissionError("Access denied: session belongs to another student.")

        # Fetch recent messages strictly scoped to this session_id
        recent_messages = (
            db.query(SessionMessage)
            .filter(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at.desc())
            .limit(max_turns * 2)
            .all()
        )

        if not recent_messages:
            return [], False, None

        # Sort deterministically chronologically; user turns sort ahead of assistant turns on microsecond ties
        chronological = sorted(
            recent_messages,
            key=lambda m: (m.created_at, 0 if m.sender_role == "user" else 1, m.id),
        )
        is_follow_up = self.is_follow_up_inquiry(current_query)

        raw_turns: List[Dict[str, str]] = []
        for m in chronological:
            if not (m.content and m.content.strip()):
                continue
            raw_turns.append({
                "role": m.sender_role,
                "content": m.content,
                "input_type": m.input_type or "text",
                "extracted_question": m.extracted_question or m.content,
            })

        # Keep most recent turns intact within character budget (avoiding mid-code truncation)
        bounded_reversed: List[Dict[str, str]] = []
        running_chars = 0
        for turn in reversed(raw_turns):
            turn_len = len(turn["content"])
            if bounded_reversed and running_chars + turn_len > max_total_chars:
                break
            bounded_reversed.append(turn)
            running_chars += turn_len
        turns = list(reversed(bounded_reversed))

        prior_context_summary = None
        if is_follow_up and chronological:
            last_assistant = next((m for m in reversed(chronological) if m.sender_role == "assistant"), None)
            last_user = next((m for m in reversed(chronological) if m.sender_role == "user"), None)

            context_parts = []
            if last_user:
                context_parts.append(f"Student previously asked: '{last_user.extracted_question or last_user.content[:150]}'")
            if last_assistant:
                math_formulas = re.findall(r'(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)', last_assistant.content)
                if math_formulas:
                    clean_formulas = [f.strip('$').strip() for f in math_formulas[:3]]
                    context_parts.append(f"Governing equations: {', '.join(clean_formulas)}")

            if context_parts:
                prior_context_summary = " | ".join(context_parts)

        return turns, is_follow_up, prior_context_summary


context_manager = ConversationContextManager()

