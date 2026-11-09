"""Template-based avatar guidance.

Task 60. Produces what Aria says about a classification, and the
`AvatarGuidance` row from Task 47.

THE SHAPE MATCHES WHAT THE FRONTEND ALREADY CONSUMES.

Task 47 flagged a mismatch and deferred the decision: the frontend's
guidance object is richer than the `AvatarGuidance` table's two columns.
`frontend/src/config/ariaGuidance.js` produces

    { summary, whyTitle, why, nextSteps[], do[], dont[], keyDefence }

while the table has `message_text` and `explanation`.

Resolved by **returning the full shape and storing a flattened version**.
Returning two fields would have forced the frontend to either restructure
its panel or discard most of the response; extending the table to seven
columns would have put presentation structure in the schema, where a
wording change becomes a migration.

So: the API answers in the shape the UI already renders, and the table
keeps a readable record for the audit trail and the Tasks 60-63 analytics.
`useAriaGuidance` becomes a one-line swap, exactly as its own comment
anticipated.

WHY TEMPLATES AND NOT AN LLM.

Same reasoning as Task 59, and it matters more here. Guidance text is
shown to a user as authoritative security advice. Generating it from a
model, using the attack prompt as input, would mean an attacker could
influence the advice our own tool gives -- a prompt injection against the
prompt-injection teacher. Fixed text cannot be steered.

WHAT THE GUIDANCE DOES NOT DO.

It never quotes or references the user's prompt. That is deliberate: the
prompt may be an attack payload, and echoing it into a panel the user
reads as trustworthy would be a stored-XSS shape of problem in a
different coat. The guidance explains the *class*, not the instance.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Per-class guidance. Mirrors the structure and tone of
# frontend/src/config/ariaGuidance.js, which was written first -- the
# frontend is the consumer, so its shape wins.
CLASS_GUIDANCE: dict[str, dict] = {
    "Safe": {
        "summary": (
            "PromptShield did not match this prompt to a supported "
            "prompt-injection class."
        ),
        "whyTitle": "Why good habits still matter",
        "why": (
            "Clear, well-structured prompts behave more predictably and make "
            "real injection attempts easier to spot — for you and for the "
            "systems you build."
        ),
        "nextSteps": [
            "Send the prompt as intended.",
            "Check it again if you later add documents, web content or tool "
            "output to the conversation.",
        ],
        "do": [
            "State the task and the output you expect",
            "Keep your instructions separate from any content you supply",
            "Review AI output before acting on it",
        ],
        "dont": [
            "Paste passwords, API keys or other secrets into prompts",
            "Treat a Safe result as cover for every kind of risk",
            "Ask the model to set aside its own rules",
        ],
    },
    "Direct Jailbreak": {
        "summary": (
            "This prompt tries to make the assistant set aside its own "
            "instructions or safety rules."
        ),
        "whyTitle": "Why this is blocked",
        "why": (
            "A direct jailbreak asks the model to stop being itself — by "
            "overriding its instructions, adopting a rule-free persona, or "
            "reframing a restricted request as fiction. The request is judged "
            "on what it ultimately asks for, not on how it is framed."
        ),
        "nextSteps": [
            "Ask the question directly, and say what you need it for.",
            "If you are researching the technique, ask how it works and how "
            "it is defended against.",
        ],
        "do": [
            "State your actual goal in plain terms",
            "Ask about a technique rather than asking the model to perform it",
            "Keep the request in one prompt rather than building up to it",
        ],
        "dont": [
            "Tell the model to ignore, forget or override its instructions",
            "Assign a persona in order to get a different answer",
            "Frame a restricted request as hypothetical or fictional",
        ],
    },
    "Indirect Injection": {
        "summary": (
            "This prompt contains content that tries to issue instructions "
            "from inside data the assistant was asked to process."
        ),
        "whyTitle": "Why this is the harder attack",
        "why": (
            "An indirect injection does not come from the person typing. It "
            "hides in a document, an email, a web page or a tool response, "
            "and relies on the assistant treating that material as "
            "instructions rather than as content. The user may never see it."
        ),
        "nextSteps": [
            "Say explicitly what you want done with the material.",
            "State that the content is data to analyse, not instructions to "
            "follow.",
        ],
        "do": [
            "Separate your instruction from the content you supply",
            "Mark fetched, pasted or emailed material as untrusted",
            "Check what an automated step actually did before relying on it",
        ],
        "dont": [
            "Pass a document straight through with no framing",
            "Let tool or API output flow into a prompt unchecked",
            "Assume content is harmless because you did not write it",
        ],
    },
}

# One line per sub-type, appended as `keyDefence`. These are the defence a
# developer should take away, and are intentionally the same lines the
# frontend already shows -- consistency matters more than variety when the
# same user may see both.
SUBTYPE_DEFENCE: dict[str, str] = {
    "Policy Evasion": (
        "Judge a request by what it ultimately asks for, not by how it is "
        "framed or split up."
    ),
    "Multi-Turn Manipulation": (
        "Evaluate the conversation as a whole — a harmless-looking turn can "
        "be one step toward a restricted request."
    ),
    "Role Override": (
        "Keep the model's assigned role fixed, and treat requests to switch "
        "tasks mid-prompt as untrusted."
    ),
    "Persona Hijacking": (
        "No persona, however it is framed, should override the model's "
        "safety rules."
    ),
    "System Prompt Overwrite": (
        "Treat system instructions as confidential and fixed — never echo or "
        "replace them on request."
    ),
    "Document Embedding": (
        "Treat text inside documents, emails and pasted files as content to "
        "analyse, never as instructions."
    ),
    "Web Content Injection": (
        "Treat fetched pages and received email as untrusted data, however "
        "legitimate the source looks."
    ),
    "Tool Output Injection": (
        "Treat tool and API responses as data — an automated step is not a "
        "trusted speaker."
    ),
}

# Appended when the sub-type is one the model cannot identify. ML Task 34
# measured Role Override at 0.00 F1 -- never predicted, with 14 of 18 test
# cases returning Policy Evasion instead. Saying so is more useful than a
# confident wrong label.
UNRELIABLE_NOTE = (
    "Note: our sub-type classifier is unreliable for this category, so the "
    "sub-type above may be inaccurate even though the main classification is "
    "not. The guidance here applies to the attack class."
)


@dataclass(frozen=True)
class Guidance:
    """Aria's guidance for one classification.

    Field names match frontend/src/config/ariaGuidance.js so
    `useAriaGuidance` can swap its source without the panel changing.
    """

    summary: str
    whyTitle: str
    why: str
    nextSteps: list[str] = field(default_factory=list)
    do: list[str] = field(default_factory=list)
    dont: list[str] = field(default_factory=list)
    keyDefence: str | None = None
    # 'backend' here; the frontend's own config reports 'general'. Lets the
    # UI show where the advice came from, and lets Task 82 tell them apart
    # while both sources coexist.
    source: str = "backend"
    # 'class' or 'subtype' -- how specific this advice is.
    scope: str = "class"

    def flatten(self) -> tuple[str, str]:
        """(message_text, explanation) for the Task 47 AvatarGuidance row.

        The table keeps a readable record rather than seven columns of
        presentation structure, where a wording change would become a
        migration.
        """
        message = self.summary
        if self.keyDefence:
            message = f"{message} {self.keyDefence}"

        parts = [self.why]
        if self.nextSteps:
            parts.append(
                "Next: " + " ".join(s.rstrip(".") + "." for s in self.nextSteps)
            )
        if self.do:
            parts.append("Do: " + "; ".join(self.do) + ".")
        if self.dont:
            parts.append("Avoid: " + "; ".join(self.dont) + ".")

        return message, " ".join(parts)


def build_guidance(
    prompt_type: str,
    subtype: str | None = None,
    subtype_reliable: bool = True,
) -> Guidance:
    """Guidance for a classification. Never references the user's prompt.

    Raises:
        ValueError: unknown prompt_type. Not silently defaulted -- a
            missing class means the taxonomies have drifted, and guessing
            would hide that.
    """
    template = CLASS_GUIDANCE.get(prompt_type)
    if template is None:
        raise ValueError(
            f"No guidance for prompt_type={prompt_type!r}. The ML and "
            f"backend label sets may have drifted."
        )

    key_defence = SUBTYPE_DEFENCE.get(subtype) if subtype else None
    why = template["why"]

    # An unreliable sub-type is disclosed rather than presented as fact.
    if subtype is not None and not subtype_reliable:
        why = f"{why} {UNRELIABLE_NOTE}"

    return Guidance(
        summary=template["summary"],
        whyTitle=template["whyTitle"],
        why=why,
        nextSteps=list(template["nextSteps"]),
        do=list(template["do"]),
        dont=list(template["dont"]),
        keyDefence=key_defence,
        scope="subtype" if key_defence else "class",
    )
