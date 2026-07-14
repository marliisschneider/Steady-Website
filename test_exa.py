from pathlib import Path

from dotenv import load_dotenv
from exa_py import Exa

script_dir = Path(__file__).resolve().parent
load_dotenv(script_dir / ".env")
load_dotenv(script_dir.parent / ".env")

exa = Exa()

QUERIES = [
    "companies hiring senior AI engineers in Austin 2026",
    "Gusto recent funding hiring news 2026",
    "Austin nutrition coaching business trends 2026",
]

for i, query in enumerate(QUERIES, start=1):
    print(f"\n{'=' * 70}")
    print(f"Query {i}: {query}")
    print("=" * 70)

    response = exa.search(query, num_results=5)

    for j, result in enumerate(response.results, start=1):
        print(f"\n{j}. {result.title}")
        print(f"   {result.url}")
