"""
AFLHR Lite - HaluEval Dataset Loader
Loads HaluEval QA and Summarization subsets and splits into dev/test sets.

HaluEval structure (per sample):
  QA:            knowledge, question, answer, hallucination ("yes"/"no")
  Summarization: document, summary, hallucination ("yes"/"no")

AI Disclosure: Development of this module was assisted by AI tools
for code structuring, debugging, and refactoring. The dataset selection,
loading strategy, and split methodology are the author's own work.
"""

import random
from pathlib import Path

from config import EXPERIMENT_SEED, DEV_SPLIT_RATIO, HALUEVAL_DATASET, DATA_DIR


def load_halueval(tasks=("qa", "summarization"), cache_dir=None):
    """Load HaluEval QA and Summarization subsets from HuggingFace.

    Each sample is independently labeled with hallucination = "yes" / "no".

    Returns:
        List of dicts with keys: sample_id, task, knowledge, question,
        response, label (1 = hallucination, 0 = valid)
    """
    from datasets import load_dataset

    if cache_dir is None:
        cache_dir = str(Path(DATA_DIR) / "halueval")

    samples = []
    sample_id = 0

    for task in tasks:
        config_name = f"{task}_samples"
        print(f"Loading HaluEval {task}...")

        # HaluEval uses "data" as the split name; fall back to "train"
        try:
            ds = load_dataset(
                HALUEVAL_DATASET, config_name, split="data",
                cache_dir=cache_dir,
            )
        except (ValueError, KeyError):
            ds = load_dataset(
                HALUEVAL_DATASET, config_name, split="train",
                cache_dir=cache_dir,
            )

        print(f"  Loaded {len(ds)} samples")

        for row in ds:
            if task == "qa":
                knowledge = row["knowledge"]
                question = row["question"]
                response = row["answer"]
            elif task == "summarization":
                knowledge = row["document"]
                question = ""  # No explicit question for summarization
                response = row["summary"]
            else:
                raise ValueError(f"Unknown task: {task}")

            label = 1 if row["hallucination"] == "yes" else 0

            samples.append({
                "sample_id": sample_id,
                "task": task,
                "knowledge": knowledge,
                "question": question,
                "response": response,
                "label": label,
            })
            sample_id += 1

    return samples


def split_dev_test(samples, dev_ratio=None, seed=None):
    """Split samples into dev and test sets.

    Args:
        samples: List of sample dicts (as returned by load_halueval)
        dev_ratio: Fraction for dev set (default from config)
        seed: Random seed (default from config)

    Returns:
        (dev_samples, test_samples) tuple
    """
    if dev_ratio is None:
        dev_ratio = DEV_SPLIT_RATIO
    if seed is None:
        seed = EXPERIMENT_SEED

    indices = list(range(len(samples)))
    random.seed(seed)
    random.shuffle(indices)

    split_idx = int(len(indices) * dev_ratio)
    dev_idx = set(indices[:split_idx])

    dev = [samples[i] for i in sorted(dev_idx)]
    test = [samples[i] for i in sorted(set(indices) - dev_idx)]

    return dev, test


if __name__ == "__main__":
    samples = load_halueval()
    dev, test = split_dev_test(samples)

    print(f"\nTotal samples: {len(samples)}")
    print(f"Dev samples:   {len(dev)}")
    print(f"Test samples:  {len(test)}")

    for task in ("qa", "summarization"):
        task_dev = [s for s in dev if s["task"] == task]
        task_test = [s for s in test if s["task"] == task]
        print(f"\n{task}:")
        print(f"  Dev:  {len(task_dev)} ({sum(s['label'] for s in task_dev)} hallucinated)")
        print(f"  Test: {len(task_test)} ({sum(s['label'] for s in task_test)} hallucinated)")

    # Print a sample for inspection
    print("\nSample QA entry:")
    qa = [s for s in samples if s["task"] == "qa"][0]
    print(f"  Knowledge: {qa['knowledge'][:100]}...")
    print(f"  Question:  {qa['question']}")
    print(f"  Response:  {qa['response'][:100]}...")
    print(f"  Label:     {qa['label']}")
