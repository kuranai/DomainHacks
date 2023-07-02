from pathlib import Path


script_dir = Path(__file__).parent
tlds_path = (script_dir / "../../data/tlds.txt").resolve()
words_path = (script_dir / "../../data/words.txt").resolve()
output_path = (script_dir / "../../data/output.txt").resolve()

tlds = []
with open(tlds_path, "r", encoding="UTF-8") as f:
    for line in f:
        tlds.append(line.strip().lower())

words = []
with open(words_path, "r", encoding="UTF-8") as f:
    for line in f:
        words.append(line.strip())

with open(output_path, "w") as f:
    for word in words:
        for tld in tlds:
            if word.endswith(tld) and word != tld:
                f.write(f"{word[:-len(tld)]}.{tld}\n")
