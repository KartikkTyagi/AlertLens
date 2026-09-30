"""
AlertLens — Full Pipeline Orchestration
=======================================
Runs all 4 pipeline stages in sequence:
  1. Data Generation (ml.data_generator)
  2. Semantic Graph Clustering (ml.clustering)
  3. Risk Scoring & MITRE Tagging (ml.ranking)
  4. Groq LLM Incident Summarization (ml.summarize)

Usage:
  python -m scripts.run_full_pipeline
  (or inside container: docker compose exec backend python -m scripts.run_full_pipeline)
"""

import sys
import time
import subprocess
import os

STAGES = [
    ("Stage 1/4: Synthetic Alert Stream Generation", "ml.data_generator"),
    ("Stage 2/4: Semantic Graph Clustering", "ml.clustering"),
    ("Stage 3/4: Risk Scoring, MITRE Tagging & Evaluation", "ml.ranking"),
    ("Stage 4/4: Groq AI Incident Summarization", "ml.summarize"),
]


def print_banner(text: str):
    width = 72
    print("\n" + "=" * width)
    print(f" {text}")
    print("=" * width + "\n")


def run_pipeline():
    total_start = time.time()
    print_banner("ALERT-LENS END-TO-END PIPELINE ORCHESTRATION")
    print(f"Python interpreter: {sys.executable}")
    print(f"Working directory:  {os.getcwd()}\n")

    for idx, (title, module_name) in enumerate(STAGES, 1):
        stage_start = time.time()
        print(f"[{idx}/{len(STAGES)}] Starting {title} ({module_name})...")
        print("-" * 72)

        try:
            cmd = [sys.executable, "-m", module_name]
            result = subprocess.run(cmd, check=True)
            elapsed = time.time() - stage_start
            print("-" * 72)
            print(f"[{idx}/{len(STAGES)}] COMPLETED: {module_name} in {elapsed:.1f}s\n")
        except subprocess.CalledProcessError as e:
            print("\n" + "!" * 72)
            print(f"ERROR: {module_name} failed with return code {e.returncode}!")
            print("!" * 72)
            sys.exit(e.returncode)

    total_elapsed = time.time() - total_start
    print_banner(f"PIPELINE COMPLETE: ALL 4 STAGES FINISHED IN {total_elapsed:.1f}s")
    print("Next steps:")
    print("  - Open http://localhost:3000 to view your triage dashboard.")
    print("  - Log in with analyst_demo (demo1234) or admin_demo (admin1234).")
    print("  - Run 'python -m ml.live_demo_feed' to demonstrate real-time alerts.\n")


if __name__ == "__main__":
    run_pipeline()
