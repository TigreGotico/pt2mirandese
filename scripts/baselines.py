"""Translate gold files with another system, for comparison: bench/<system>/<gold file> holds id and hypothesis.

Apertium has no Mirandese pair, so the one other system is madlad: MADLAD-400 3B (Google, Apache-2.0), the
model that MinT, the Wikimedia translation service, serves for Portuguese to Mirandese. The CTranslate2 build
santhosh/madlad400-3b-ct2 runs on the CPU in int8 with greedy decoding, and the target tag <2mwl>.

    python scripts/baselines.py madlad gold/wikimedia_test.tsv ...
"""
import csv
import sys
from pathlib import Path

BENCH = Path(__file__).parent.parent / "bench"


def madlad():
    import ctranslate2
    import sentencepiece
    from huggingface_hub import snapshot_download

    path = snapshot_download("santhosh/madlad400-3b-ct2")
    model = ctranslate2.Translator(path, device="cpu", compute_type="int8")
    sp = sentencepiece.SentencePieceProcessor(model_file=f"{path}/sentencepiece.model")

    def run(texts):
        # The target tag is part of the source text, which sentencepiece splits into "▁" and "<2mwl>".
        batch = [sp.encode("<2mwl> " + t, out_type=str) + ["</s>"] for t in texts]
        out = model.translate_batch(batch, max_batch_size=16, beam_size=1, max_decoding_length=512)
        return [sp.decode(r.hypotheses[0]) for r in out]
    return run


def main():
    system, paths = sys.argv[1], sys.argv[2:]
    run = {"madlad": madlad}[system]()
    out_dir = BENCH / system
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in map(Path, paths):
        rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines(), delimiter="\t"))
        texts = [" ".join(r["pt"].split()) for r in rows]
        hyps = []
        for k in range(0, len(texts), 32):
            hyps += run(texts[k:k + 32])
        with open(out_dir / path.name, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["id", "hyp"])
            w.writerows((r["id"], h) for r, h in zip(rows, hyps))
        print(f"{system} {path.name}: rows in={len(rows)} out={len(hyps)}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
