"""
enrich_agent.py — per-lead enrichment loop.

For one lead: Observe -> Think -> Act -> Check, bounded to 2 tool calls.
  1. research_lead() (the SteadyLeadResearcher Skill) is always tried first.
  2. If industry AND pain_points are still both empty, and the email is a
     real company domain, one targeted Exa search is tried as a second and
     final tool call.
  3. If there's enough grounded info to draft something specific, draft it,
     save it, and push it to Gmail as a draft. Otherwise save whatever was
     found and mark the lead 'needs_manual_followup'.

Run standalone to process every lead with status='new'; import enrich_lead()
to run it on a single lead id.
"""

import os
import sys
import time
import traceback

from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic
from composio import Composio
from composio_client import NotFoundError
from exa_py import Exa
from rich.console import Console
from rich.panel import Panel
from supabase import create_client

from steady_lead_researcher import LeadResearchError, research_lead

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
# Writes bypass RLS via the service role key — the anon key (same one baked
# into the public site's config.js) intentionally has no UPDATE grant on
# steady_leads, so it can't write here.
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]
COMPOSIO_API_KEY = os.environ["COMPOSIO_API_KEY"]

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
MAX_TOOL_CALLS = 2

# Live-teaching pacing: real API calls (research_lead, Exa) usually cover this
# on their own, but the panel prints themselves are instant, and the "skip
# Exa" branch has no API call at all — so pause after every panel to leave
# room to talk it through out loud. Set PANEL_PAUSE_SECONDS=0 to run at full
# speed (e.g. for a batch job with no audience).
PANEL_PAUSE_SECONDS = float(os.environ.get("PANEL_PAUSE_SECONDS", "1.5"))
COMPOSIO_USER_ID = "pg-test-d0673ae0-6485-4aaa-9241-4cedfadfb7f1"
GMAIL_DRAFT_SLUG = "GMAIL_CREATE_EMAIL_DRAFT"
GMAIL_SEND_SLUG = "GMAIL_SEND_EMAIL"
DIGEST_RECIPIENT = "steadycoaching.co@gmail.com"

# Same list SteadyLeadResearcher uses: a search against a personal inbox
# provider reveals nothing about someone's employer.
PERSONAL_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "aol.com",
}

# Reserved/placeholder domains from test data (RFC 2606 examples plus common
# QA seeds) — a search against these returns noise, not a real company.
PLACEHOLDER_EMAIL_DOMAINS = {
    "example.com", "example.org", "example.net", "test.com",
}

NON_COMPANY_EMAIL_DOMAINS = PERSONAL_EMAIL_DOMAINS | PLACEHOLDER_EMAIL_DOMAINS

DRAFT_SYSTEM_PROMPT = (
    "You are a nutrition coach writing a short, personalized follow-up to a warm "
    "lead. Write 2-3 sentences that reference something SPECIFIC and REAL from "
    "the research below — never a generic compliment or an invented detail. "
    "Offer a free 20-minute discovery call. Body text only, no greeting, no "
    "signature."
)

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
exa = Exa(EXA_API_KEY)
anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)
composio = Composio(api_key=COMPOSIO_API_KEY)

console = Console()


class EnrichmentError(Exception):
    """Raised when a lead can't be looked up at all."""


def _fields_lines(fields):
    lines = [
        f"industry:    {fields['industry']!r}",
        f"pain_points: {fields['pain_points']!r}",
        f"hook:        {fields['hook']!r}",
    ]
    if fields.get("exa_notes") is not None:
        lines.append(f"exa_notes:   {fields['exa_notes']!r}")
    return "\n".join(lines)


def observe_panel(iteration, fields, note):
    body = f"{_fields_lines(fields)}\n\n[italic]{note}[/italic]"
    console.print(
        Panel(body, title=f"OBSERVE · iteration {iteration}", border_style="blue", title_align="left")
    )
    time.sleep(PANEL_PAUSE_SECONDS)


def act_panel(iteration, tool, reasoning, call):
    body = f"[bold]reasoning:[/bold] {reasoning}\n[bold]tool:[/bold] {tool}\n[bold]calling:[/bold] {call}"
    console.print(
        Panel(body, title=f"ACT · iteration {iteration}", border_style="yellow", title_align="left")
    )
    time.sleep(PANEL_PAUSE_SECONDS)


def check_panel(iteration, fields, stopping, verdict):
    style = "green" if stopping else "yellow"
    decision = "STOP — enough to draft" if stopping else "LOOP AGAIN"
    body = f"{_fields_lines(fields)}\n\n[bold]{verdict}[/bold]\n[bold {style}]→ {decision}[/bold {style}]"
    console.print(
        Panel(
            body,
            title=f"CHECK · iteration {iteration} · [{style}]{decision}[/{style}]",
            border_style=style,
            title_align="left",
        )
    )
    time.sleep(PANEL_PAUSE_SECONDS)


def stopped_banner(name, email, status, reason, draft=None):
    color = {"drafted": "green", "needs_manual_followup": "red"}.get(status, "white")
    body = f"[bold]{name}[/bold]  <{email}>\n\nstatus: [bold {color}]{status}[/bold {color}]\nreason: {reason}"
    if draft:
        body += f"\n\n[bold]draft:[/bold]\n{draft}"
    console.print(
        Panel(body, title=f"■ STOPPED — {status.upper()}", border_style=color, title_align="left", expand=False)
    )
    console.print()


def is_company_domain(email):
    if not email or "@" not in email:
        return False
    return email.split("@", 1)[1].lower() not in NON_COMPANY_EMAIL_DOMAINS


def has_enough_to_draft(fields):
    return bool(fields["pain_points"] or fields["hook"] or fields["industry"] or fields["exa_notes"])


def fetch_lead(lead_id):
    rows = supabase.table("steady_leads").select("*").eq("id", lead_id).execute().data
    if not rows:
        raise EnrichmentError(f"No lead found with id={lead_id!r}")
    return rows[0]


def exa_company_search(email):
    domain = email.split("@", 1)[1]
    # include_domains pins results to this exact site — a free-text query on
    # the domain string alone fuzzy-matches on the name and can surface an
    # unrelated same-named company for under-indexed domains.
    results = exa.search(
        "company news 2026", num_results=3, include_domains=[domain]
    ).results
    return "; ".join(f"{r.title} ({r.url})" for r in results) or None


def draft_follow_up(lead, fields):
    findings = []
    if fields["industry"]:
        findings.append(f"Industry: {fields['industry']}")
    if fields["pain_points"]:
        findings.append(f"Pain points: {', '.join(fields['pain_points'])}")
    if fields["hook"]:
        findings.append(f"Conversation hook: {fields['hook']}")
    if fields["exa_notes"]:
        findings.append(f"Additional research: {fields['exa_notes']}")

    user_content = (
        f"Lead name: {lead.get('name')}\n"
        f"Lead email: {lead.get('email')}\n"
        f"Lead source: {lead.get('source')}\n"
        f"Lead's own message: {lead.get('message') or '(none)'}\n\n"
        "Grounded research:\n" + "\n".join(findings)
    )
    message = anthropic.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=300,
        system=DRAFT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    return "".join(b.text for b in message.content if b.type == "text").strip()


def find_gmail_draft_slug():
    """Fallback: the configured slug wasn't found, so look up what gmail toolkit
    actually exposes right now and report it instead of guessing."""
    tools = composio.tools.get_raw_composio_tools(toolkits=["gmail"])
    slugs = [tool.slug for tool in tools]
    print(f"  Gmail toolkit slugs available: {slugs}")
    return slugs


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


def save_enrichment(lead_id, fields, draft, status):
    resp = (
        supabase_admin.table("steady_leads")
        .update(
            {
                "industry": fields["industry"],
                "pain_points": fields["pain_points"],
                "hook": fields["hook"],
                "draft_message": draft,
                "status": status,
            }
        )
        .eq("id", lead_id)
        .execute()
    )
    if not resp.data:
        raise EnrichmentError(f"Update affected 0 rows for lead id={lead_id!r} — check RLS/service key")


def finish_with_draft(lead, fields, tool_calls):
    draft = draft_follow_up(lead, fields)
    save_enrichment(lead["id"], fields, draft, status="drafted")
    try:
        save_gmail_draft(lead, draft)
        console.print("[green]Gmail draft saved.[/green]")
    except Exception as exc:
        console.print(f"[yellow]Gmail draft FAILED ({exc}) — draft is still saved in Supabase.[/yellow]")
    return {"status": "drafted", "fields": fields, "draft": draft, "reason": None}


def enrich_lead(lead_id):
    lead = fetch_lead(lead_id)
    name, email = lead.get("name"), lead.get("email")
    fields = {
        "industry": lead.get("industry"),
        "pain_points": lead.get("pain_points"),
        "hook": lead.get("hook"),
        "exa_notes": None,
    }

    console.rule(f"[bold]{name}[/bold]  <{email}>  ·  source={lead.get('source')}")

    observe_panel(1, fields, "no research done yet on this pass")
    act_panel(
        1,
        "research_lead()  (SteadyLeadResearcher Skill)",
        "always tried first — it's the primary source",
        "research_lead(name, email, source, message)",
    )
    try:
        profile = research_lead(name, email, source=lead.get("source"), message=lead.get("message"))
        fields["industry"] = fields["industry"] or profile.get("likely_industry")
        fields["pain_points"] = fields["pain_points"] or profile.get("potential_pain_points")
        fields["hook"] = fields["hook"] or profile.get("one_conversation_hook")
    except LeadResearchError as exc:
        console.print(f"[red]research_lead() failed: {exc}[/red]")

    stop_now = has_enough_to_draft(fields)
    check_panel(1, fields, stop_now, "enough grounded info" if stop_now else "industry and pain_points both still empty")

    if stop_now:
        result = finish_with_draft(lead, fields, tool_calls=1)
        stopped_banner(name, email, result["status"], "enough grounded info after 1 tool call", result["draft"])
        return result

    observe_panel(2, fields, "industry and pain_points both still empty")
    if is_company_domain(email):
        act_panel(
            2,
            "exa.search(include_domains=[domain])",
            f"{email!r} is a real company domain — try one targeted Exa search before giving up",
            "exa_company_search(email)",
        )
        try:
            fields["exa_notes"] = exa_company_search(email)
        except Exception as exc:
            console.print(f"[red]Exa search failed: {exc}[/red]")
        reason = "no grounded info from the Skill or a follow-up Exa search"
    else:
        act_panel(
            2,
            "(skipped — no tool call)",
            f"{email!r} is a personal inbox provider — a search here won't reveal anything real",
            "n/a",
        )
        reason = f"no grounded info from the Skill, and {email!r} isn't a real company domain to search further"

    stop_now = has_enough_to_draft(fields)
    check_panel(2, fields, stop_now, "enough grounded info" if stop_now else "still not enough after 2 tool calls")

    if stop_now:
        result = finish_with_draft(lead, fields, tool_calls=2)
        stopped_banner(name, email, result["status"], "enough grounded info after 2 tool calls", result["draft"])
        return result

    save_enrichment(lead["id"], fields, draft=None, status="needs_manual_followup")
    result = {"status": "needs_manual_followup", "fields": fields, "draft": None, "reason": reason}
    stopped_banner(name, email, result["status"], reason)
    return result


def send_digest(needs_attention, drafted_count):
    subject = f"Steady enrichment digest — {len(needs_attention)} lead(s) need manual follow-up"
    lines = [f"Batch finished: {drafted_count} drafted, {len(needs_attention)} need manual follow-up.", ""]
    for item in needs_attention:
        lines.append(f"- {item['name']} <{item['email']}>: {item['reason']}")
    body = "\n".join(lines)

    try:
        composio.tools.execute(
            GMAIL_SEND_SLUG,
            {"recipient_email": DIGEST_RECIPIENT, "subject": subject, "body": body},
            user_id=COMPOSIO_USER_ID,
            dangerously_skip_version_check=True,
        )
        print(f"✓ digest email sent to {DIGEST_RECIPIENT} ({len(needs_attention)} lead(s))\n")
    except Exception as exc:
        print(f"✗ digest email FAILED to send: {exc}\n")


def run_batch():
    leads = supabase.table("steady_leads").select("id, name, email").eq("status", "new").execute().data
    print(f"Fetched {len(leads)} lead(s) with status='new'\n")

    drafted_count = 0
    needs_attention = []

    for lead in leads:
        try:
            result = enrich_lead(lead["id"])
        except Exception as exc:
            print(f"✗ error processing lead id={lead['id']}:")
            traceback.print_exc()
            print()
            needs_attention.append(
                {"name": lead.get("name"), "email": lead.get("email"), "reason": f"processing error: {exc}"}
            )
            continue

        if result["status"] == "drafted":
            drafted_count += 1
        else:
            needs_attention.append({"name": lead.get("name"), "email": lead.get("email"), "reason": result["reason"]})

    console.rule(f"[bold]Batch done[/bold] — {drafted_count} drafted, {len(needs_attention)} need manual follow-up", style="bold")
    console.print()

    if needs_attention:
        send_digest(needs_attention, drafted_count)
    else:
        console.print("[green]Everything drafted cleanly — no digest email needed.[/green]\n")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        enrich_lead(sys.argv[1])
    else:
        run_batch()
