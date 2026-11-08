"""Context management service: preserves relevant conversation history for follow-ups while isolating sessions."""

import re
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.session import StudySession, SessionMessage


# Pronouns and keywords indicating that the student inquiry references prior turn context
ANAPHORIC_PATTERNS = [
    r'\b(that|it|this|the above|previous|earlier)\b',
    r'\b(why|how come|what about|how about|what if)\b',
    r'\b(step\s*\d+|formula|equation|result|solution)\b',
    r'\b(repeat|continue|elaborate|simplify\s+it|explain\s+more)\b'
]


class ConversationContextManager:
    """Manages dialogue state and anaphoric resolution within isolated study sessions."""

    def is_follow_up_inquiry(self, query: str) -> bool:
        """Detect whether student question relies on context from earlier messages."""
        q_lower = query.lower()
        return any(re.search(pat, q_lower) for pat in ANAPHORIC_PATTERNS)

    def extract_relevant_context(
        self,
        session_id: Optional[str],
        current_query: str,
        db: Session,
        max_turns: int = 4
    ) -> Tuple[List[Dict[str, str]], bool, Optional[str]]:
        """
        Retrieve relevant prior dialogue history strictly bounded within session_id.
        
        Returns:
            - List of formatted turn dicts [{'role': 'user'|'assistant', 'content': '...'}]
            - is_follow_up (bool)
            - relevant_summary (Optional[str])
        """
        if not session_id:
            # New or unattached inquiry - strict zero context bleed
            return [], False, None

        # Fetch recent messages within the specified session only
        recent_messages = (
            db.query(SessionMessage)
            .filter(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at.desc())
            .limit(max_turns * 2)
            .all()
        )

        if not recent_messages:
            return [], False, None

        # Reverse to chronological order
        chronological = list(reversed(recent_messages))
        is_follow_up = self.is_follow_up_inquiry(current_query)

        turns = []
        prior_context_summary = None

        for m in chronological:
            turns.append({
                "role": m.sender_role,
                "content": m.content,
                "input_type": m.input_type or "text",
                "extracted_question": m.extracted_question or m.content
            })

        # If follow-up, extract key formulas and targets from immediate prior assistant turn
        if is_follow_up and chronological:
            last_assistant = next((m for m in reversed(chronological) if m.sender_role == "assistant"), None)
            last_user = next((m for m in reversed(chronological) if m.sender_role == "user"), None)

            context_parts = []
            if last_user:
                context_parts.append(f"Student previously asked: '{last_user.extracted_question or last_user.content[:150]}'")
            if last_assistant:
                # Extract any LaTeX formulas from prior answer
                math_formulas = re.findall(r'(\$\$[\s\S]*?\$\$|\$[^\$]+?\$)', last_assistant.content)
                if math_formulas:
                    clean_formulas = [f.strip('$').strip() for f in math_formulas[:3]]
                    context_parts.append(f"Governing equations: {', '.join(clean_formulas)}")

            if context_parts:
                prior_context_summary = " | ".join(context_parts)

        return turns, is_follow_up, prior_context_summary


context_manager = ConversationContextManager()

