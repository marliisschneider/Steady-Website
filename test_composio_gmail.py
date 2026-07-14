"""Test that Composio's Gmail connection is real by creating a draft."""

import os
import sys
import traceback

from dotenv import load_dotenv

load_dotenv()

USER_ID = "pg-test-d0673ae0-6485-4aaa-9241-4cedfadfb7f1"
TO = "steadycoaching.co@gmail.com"
SUBJECT = "Composio connection test"
BODY = (
    "If this shows up in Drafts folder of steadycoaching.co@gmail.com, "
    "the connection is real and tied to that inbox."
)


def main():
    api_key = os.environ.get("COMPOSIO_API_KEY")
    if not api_key:
        print("FAILED: COMPOSIO_API_KEY is not set (checked .env and environment).")
        sys.exit(1)

    from composio import Composio

    composio = Composio(api_key=api_key)

    result = composio.tools.execute(
        "GMAIL_CREATE_EMAIL_DRAFT",
        user_id=USER_ID,
        arguments={
            "recipient_email": TO,
            "subject": SUBJECT,
            "body": BODY,
        },
        dangerously_skip_version_check=True,
    )

    if not result.get("successful", False):
        print("FAILED: Composio reported the tool call as unsuccessful.")
        print(f"Error: {result.get('error')}")
        print(f"Full result: {result}")
        sys.exit(1)

    data = result.get("data", {})
    draft_id = None
    if isinstance(data, dict):
        nested_draft = data.get("draft")
        draft_id = (
            data.get("draft_id")
            or data.get("id")
            or data.get("draftId")
            or (nested_draft.get("id") if isinstance(nested_draft, dict) else None)
        )

    print("SUCCESS: Gmail draft created via Composio.")
    print(f"Draft ID: {draft_id if draft_id else '(not found in expected fields, see full data below)'}")
    print(f"To: {TO}")
    print(f"Subject: {SUBJECT}")
    print(f"Full response data: {data}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("FAILED: Unhandled exception while creating the Gmail draft.")
        traceback.print_exc()
        sys.exit(1)
