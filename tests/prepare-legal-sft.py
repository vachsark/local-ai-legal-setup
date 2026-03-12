#!/usr/bin/env python3
"""Convert raw legal grammar training data into chat-format JSONL for SFT."""
import json
import os
import random
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    data_dir = os.path.join(
        os.path.expanduser("~"),
        "Documents/TestVault/Projects/ClaudeLab/training-data/legal-grammar",
    )
    combined_file = os.path.join(data_dir, "combined-raw.jsonl")
    system_prompt_file = os.path.join(SCRIPT_DIR, "grammar-sft-system-prompt.txt")

    if not os.path.exists(combined_file):
        print(f"Error: {combined_file} not found. Run gen-grammar-data.sh first.")
        sys.exit(1)

    with open(system_prompt_file) as f:
        system_prompt = f.read().strip()

    # Load and validate
    examples = []
    skipped = 0
    with open(combined_file) as f:
        for line in f:
            item = json.loads(line)
            output = item.get("output", "")
            # Basic validation: must have output sections
            if not output or len(output) < 50:
                skipped += 1
                continue
            if "CRITICAL ISSUES" not in output and "GRAMMAR" not in output:
                skipped += 1
                continue
            examples.append(item)

    print(f"Loaded {len(examples)} valid examples, skipped {skipped}")

    # Convert to chat format
    chat_examples = []
    for item in examples:
        # Clean the output: strip trailing newlines from Claude's response
        output = item["output"].strip()
        user_input = item["user_input"].strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": output},
        ]
        chat_examples.append({
            "messages": messages,
            "metadata": {"batch_id": item["batch_id"]},
        })

    # Shuffle and split 90/10
    random.seed(42)
    random.shuffle(chat_examples)
    split_idx = max(1, int(len(chat_examples) * 0.9))
    train = chat_examples[:split_idx]
    val = chat_examples[split_idx:]

    # Write
    for filename, data in [
        ("sft-dataset.jsonl", chat_examples),
        ("sft-train.jsonl", train),
        ("sft-val.jsonl", val),
    ]:
        path = os.path.join(data_dir, filename)
        with open(path, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

    print(f"SFT dataset: {len(chat_examples)} total")
    print(f"  Train: {len(train)} → {os.path.join(data_dir, 'sft-train.jsonl')}")
    print(f"  Val:   {len(val)} → {os.path.join(data_dir, 'sft-val.jsonl')}")


if __name__ == "__main__":
    main()
