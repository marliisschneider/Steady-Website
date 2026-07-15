import argparse
import json
import sys

from steady_lead_researcher import LeadResearchError, research_lead


def main():
    parser = argparse.ArgumentParser(description="Research a Steady lead via SteadyLeadResearcher")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--source", default=None)
    parser.add_argument("--message", default=None)
    args = parser.parse_args()

    try:
        profile = research_lead(args.name, args.email, source=args.source, message=args.message)
    except LeadResearchError as exc:
        print(json.dumps({"error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        sys.exit(1)

    print(json.dumps(profile, indent=2))


if __name__ == "__main__":
    main()
