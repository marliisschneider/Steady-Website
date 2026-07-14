import copy
import json
import os
import time

from dotenv import load_dotenv

load_dotenv()

from anthropic import (
    Anthropic,
    APIConnectionError,
    InternalServerError,
    OverloadedError,
    RateLimitError,
)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_SEARCHES = 3
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1

SUBMIT_TOOL_NAME = "submit_lead_profile"

SYSTEM_PROMPT = (
    "You are a nutrition coach researching leads. You'll be given a lead's name, "
    "email domain, the page on the site they submitted the form from (source), and "
    "sometimes a message they wrote in their own words about what's going on for "
    "them. "
    f"When you have enough information, call {SUBMIT_TOOL_NAME} exactly once with "
    "your findings.\n\n"
    "The lead's own message is your most reliable evidence — when present, base "
    "potential_pain_points directly on what they actually wrote, and make "
    "one_conversation_hook reference something specific from it. The source page "
    "is also real, known information you may reference (e.g. they came from a "
    "corporate wellness inquiry vs. a 1:1 coaching page).\n\n"
    "Only use web_search to find likely_industry if the email domain is a real "
    "company domain — not a personal provider (gmail.com, yahoo.com, outlook.com, "
    "hotmail.com, icloud.com, aol.com, and similar). Personal email providers "
    "reveal nothing about someone's employer or industry. For a personal domain "
    "with no message, likely_industry and potential_pain_points MUST be null — "
    "do not invent an industry, pain point, or personal detail (assumed "
    "profession, career stage, life event) that wasn't explicitly stated in their "
    "message or actually surfaced by search. A null field is correct and expected "
    "when the evidence isn't there; a fabricated one is not."
)

WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": MAX_SEARCHES,
}

SUBMIT_TOOL = {
    "name": SUBMIT_TOOL_NAME,
    "description": "Submit the researched lead profile. Call this exactly once, after searching.",
    "input_schema": {
        "type": "object",
        "properties": {
            "likely_industry": {"type": ["string", "null"]},
            "potential_pain_points": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "one_conversation_hook": {"type": ["string", "null"]},
        },
        "required": ["likely_industry", "potential_pain_points", "one_conversation_hook"],
        "additionalProperties": False,
    },
    "strict": True,
}

# Transient failures worth retrying; anything else (bad request, auth, not found) is not.
RETRYABLE_ERRORS = (
    APIConnectionError,
    RateLimitError,
    OverloadedError,
    InternalServerError,
)


class LeadResearchError(Exception):
    """Base class for all SteadyLeadResearcher failures."""


class InvalidLeadInputError(LeadResearchError):
    """Lead name or email is missing/malformed."""


class LeadResearchAPIError(LeadResearchError):
    """The Anthropic API call failed and retries were exhausted (or failed non-retryably)."""


class LeadResearchParseError(LeadResearchError):
    """Claude never produced a valid submit_lead_profile call."""


class SteadyLeadResearcher:
    """Researches a lead's company via web search and returns a structured JSON profile."""

    def __init__(
        self,
        api_key=None,
        model=CLAUDE_MODEL,
        max_searches=MAX_SEARCHES,
        max_retries=MAX_RETRIES,
        enable_cache=True,
    ):
        self.client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model
        self.max_searches = max_searches
        self.max_retries = max_retries
        self.enable_cache = enable_cache
        self._cache = {}

    def research(self, name, email, source=None, message=None):
        name, email, domain = self._validate_input(name, email)

        cache_key = (email.lower(), source or "", message or "")
        if self.enable_cache and cache_key in self._cache:
            return copy.deepcopy(self._cache[cache_key])

        user_content = f"Name: {name}\nEmail domain: {domain}\nSource page: {source or 'unknown'}\n"
        user_content += f"Lead's message: {message}" if message else "Lead's message: (none provided)"
        messages = [{"role": "user", "content": user_content}]
        response = self._create_with_retry(messages)
        profile = self._extract_submit_input(response)

        if profile is None:
            # One bounded, forced follow-up — not a retry loop. If the model
            # searched but didn't submit, force the tool call explicitly.
            messages.append({"role": "assistant", "content": response.content})
            messages.append(
                {"role": "user", "content": f"Call {SUBMIT_TOOL_NAME} now with your findings."}
            )
            response = self._create_with_retry(
                messages, tool_choice={"type": "tool", "name": SUBMIT_TOOL_NAME}
            )
            profile = self._extract_submit_input(response)

        if profile is None:
            raise LeadResearchParseError(
                f"Claude never called {SUBMIT_TOOL_NAME} for lead {email!r}"
            )

        profile = self._validate_profile(profile)

        if self.enable_cache:
            self._cache[cache_key] = profile

        return copy.deepcopy(profile)

    @staticmethod
    def _validate_input(name, email):
        if not name or not isinstance(name, str) or not name.strip():
            raise InvalidLeadInputError(f"Invalid lead name: {name!r}")
        if not email or not isinstance(email, str) or email.count("@") != 1:
            raise InvalidLeadInputError(f"Invalid lead email: {email!r}")
        local, domain = email.split("@", 1)
        if not local or not domain or "." not in domain:
            raise InvalidLeadInputError(f"Invalid lead email: {email!r}")
        return name.strip(), email.strip(), domain.strip()

    def _create_with_retry(self, messages, tool_choice=None):
        kwargs = dict(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=[WEB_SEARCH_TOOL, SUBMIT_TOOL],
            messages=messages,
        )
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.client.messages.create(**kwargs)
            except RETRYABLE_ERRORS as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(RETRY_BACKOFF_SECONDS * (2 ** (attempt - 1)))
            except Exception as exc:
                raise LeadResearchAPIError(
                    f"Non-retryable Anthropic API error: {exc}"
                ) from exc

        raise LeadResearchAPIError(
            f"Anthropic API failed after {self.max_retries} attempts: {last_error}"
        ) from last_error

    @staticmethod
    def _extract_submit_input(response):
        for block in response.content:
            if block.type == "tool_use" and block.name == SUBMIT_TOOL_NAME:
                return block.input
        return None

    @staticmethod
    def _validate_profile(profile):
        pain_points = profile.get("potential_pain_points")
        if isinstance(pain_points, str):
            pain_points = [pain_points]
        if pain_points is not None:
            if not isinstance(pain_points, list) or not all(
                isinstance(p, str) for p in pain_points
            ):
                raise LeadResearchParseError(
                    f"potential_pain_points is not a list of strings: {pain_points!r}"
                )
            pain_points = pain_points[:3] or None

        return {
            "likely_industry": profile.get("likely_industry"),
            "potential_pain_points": pain_points,
            "one_conversation_hook": profile.get("one_conversation_hook"),
        }


def research_lead(name, email, source=None, message=None):
    return SteadyLeadResearcher().research(name, email, source=source, message=message)


if __name__ == "__main__":
    # Three real shapes a Steady lead actually takes:
    #  1. Personal email + a real intake message -> grounded, no guessing needed
    #  2. Personal email + no message -> null fields, guardrail still holds
    #  3. Company email (Corporate Wellness inquiry) -> web_search path still works
    test_leads = [
        {
            "name": "Sarah Kim",
            "email": "sarah.kim88@gmail.com",
            "source": "coaching",
            "message": (
                "I've tried keto and intermittent fasting but nothing sticks with my "
                "travel schedule. Constant bloating and a 3pm energy crash most days."
            ),
        },
        {
            "name": "Derek Foss",
            "email": "dfoss@yahoo.com",
            "source": "pantry-reset",
            "message": None,
        },
        {
            "name": "Priya Patel",
            "email": "priya@northshorewellness.com",
            "source": "contact",
            "message": "Looking into corporate wellness options for our team of 40.",
        },
    ]

    researcher = SteadyLeadResearcher()

    for lead in test_leads:
        print(f"--- {lead['name']} <{lead['email']}> (source={lead['source']}) ---")
        try:
            profile = researcher.research(
                lead["name"], lead["email"], source=lead["source"], message=lead["message"]
            )
            print(json.dumps(profile, indent=2))
        except LeadResearchError as exc:
            print(f"  ✗ {type(exc).__name__}: {exc}")
        print()
