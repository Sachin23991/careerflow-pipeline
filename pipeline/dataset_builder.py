import json

filtered = json.load(open("pipeline/filtered.json"))
out = open("pipeline/train.jsonl", "w")

for n in filtered:
    prompt = f"Explain this news in simple terms:\n{n['summary']}\n\nAnswer:"
    completion = " " + n["summary"]
    out.write(json.dumps({"prompt": prompt, "completion": completion}) + "\n")

out.close()
