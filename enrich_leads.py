import os
import traceback

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic
from composio import Composio
from composio_client import NotFoundError
from exa_py import Exa
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]
COMPOSIO_API_KEY = os.environ["COMPOSIO_API_KEY"]

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
COMPOSIO_USER_ID = "pg-test-d0673ae0-6485-4aaa-9241-4cedfadfb7f1"
GMAIL_DRAFT_SLUG = "GMAIL_CREATE_EMAIL_DRAFT"

SYSTEM_PROMPT = (
    "You are a nutrition coach following up with a warm lead. Given the lead info "
    "and what you found searching about their company, write a personalized "
    "2-sentence follow-up that MUST reference something specific from the search "
    "results. Offer a free 20-minute discovery call. Just body text, no greeting, "
    "no signature."
)

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
exa = Exa(EXA_API_KEY)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
composio = Composio(api_key=COMPOSIO_API_KEY)


def find_gmail_draft_slug():
    """Fallback: the configured slug wasn't found, so look up what gmail toolkit
    actually exposes right now and report it instead of guessing."""
    tools = composio.tools.get_raw_composio_tools(toolkits=["gmail"])
    slugs = [tool.slug for tool in tools]
    print(f"  Gmail toolkit slugs available: {slugs}")
    return slugs


def search_company(email):
    domain = email.split("@", 1)[1]
    response = exa.search(f"{domain} recent news 2026", num_results=3)
    return domain, response.results


def draft_follow_up(lead, results):
    findings = "\n".join(f"- {r.title} ({r.url})" for r in results) or "- No results found."
    user_content = (
        f"Lead name: {lead.get('name')}\n"
        f"Lead email: {lead.get('email')}\n"
        f"Lead source: {lead.get('source')}\n\n"
        f"Search findings about their company:\n{findings}"
    )
    message = anthropic.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(block.text for block in message.content if block.type == "text").strip()


def save_gmail_draft(lead, body):
    try:
        result = composio.tools.execute(
            GMAIL_DRAFT_SLUG,
            {
                "recipient_email": lead["email"],
                "subject": "Following up — quick nutrition Q",
                "body": body,
            },
            user_id=COMPOSIO_USER_ID,
            dangerously_skip_version_check=True,
        )
    except NotFoundError:
        find_gmail_draft_slug()
        raise

    if not result.get("successful", True):
        raise RuntimeError(f"Gmail draft creation failed: {result.get('error')}")
    return result


def run():
    leads = supabase.table("steady_leads").select("*").eq("status", "new").execute().data
    print(f"Fetched {len(leads)} lead(s) with status='new'\n")

    for lead in leads:
        email = lead.get("email", "")
        print(f"--- Lead: {lead.get('name')} <{email}> ---")
        try:
            print("  ✓ read")

            domain, results = search_company(email)
            top_title = results[0].title if results else "(no results)"
            print(f"  ✓ searched — domain={domain}, top result: {top_title}")

            draft = draft_follow_up(lead, results)
            print(f"  ✓ drafted — {draft}")

            save_gmail_draft(lead, draft)
            print("  ✓ Gmail draft saved")

        except Exception:
            print(f"  ✗ error processing lead {email}:")
            traceback.print_exc()
            continue

        print()


if __name__ == "__main__":
    run()
