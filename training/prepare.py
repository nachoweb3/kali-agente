"""Build an executable, attributed seed corpus; never claims model-generated success."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

# Different task families are kept separate, rather than randomly splitting paraphrases.
CASES = [
    (
        "chunks",
        "train",
        "Divide una lista en bloques de n elementos; rechaza n <= 0.",
        "def solve(items, n):\n    if n <= 0:\n        raise ValueError('n must be positive')\n    return [items[i:i+n] for i in range(0, len(items), n)]\n",
        "assert solve([1,2,3,4,5],2)==[[1,2],[3,4],[5]]\nassert solve([],2)==[]\ntry:\n    solve([1],0)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('invalid size accepted')\n",
    ),
    (
        "clamp",
        "train",
        "Limita un numero al intervalo cerrado [lo, hi]; rechaza lo > hi.",
        "def solve(value, lo, hi):\n    if lo > hi:\n        raise ValueError('invalid interval')\n    return min(hi, max(lo, value))\n",
        "assert solve(-5,0,10)==0\nassert solve(3,0,10)==3\nassert solve(20,0,10)==10\ntry:\n    solve(1,3,2)\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('invalid interval accepted')\n",
    ),
    (
        "histogram",
        "train",
        "Cuenta las apariciones de cada elemento hashable sin cambiar la entrada.",
        "def solve(items):\n    result = {}\n    for item in items:\n        result[item] = result.get(item, 0) + 1\n    return result\n",
        "items=['a','b','a']\nassert solve(items)=={'a':2,'b':1}\nassert items==['a','b','a']\nassert solve([])=={}\n",
    ),
    (
        "transpose",
        "train",
        "Transpon una matriz rectangular; rechaza filas de distinta longitud.",
        "def solve(rows):\n    if not rows:\n        return []\n    if any(len(row) != len(rows[0]) for row in rows):\n        raise ValueError('ragged matrix')\n    return [list(column) for column in zip(*rows)]\n",
        "assert solve([[1,2],[3,4]])==[[1,3],[2,4]]\nassert solve([])==[]\ntry:\n    solve([[1],[2,3]])\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('ragged matrix accepted')\n",
    ),
    (
        "partition",
        "train",
        "Separa numeros pares e impares conservando su orden y sin mutar la entrada.",
        "def solve(items):\n    return ([x for x in items if x % 2 == 0], [x for x in items if x % 2 != 0])\n",
        "items=[3,2,1,4]\nassert solve(items)==([2,4],[3,1])\nassert items==[3,2,1,4]\nassert solve([])==([],[])\n",
    ),
    (
        "flatten",
        "train",
        "Aplana exactamente un nivel de una lista de listas; devuelve una lista nueva.",
        "def solve(rows):\n    return [item for row in rows for item in row]\n",
        "assert solve([[1,2],[],[3]])==[1,2,3]\nassert solve([])==[]\nassert solve([[[1]]])==[[1]]\n",
    ),
    (
        "rotate",
        "train",
        "Rota una lista k posiciones a la derecha; admite k negativo y lista vacia.",
        "def solve(items, k):\n    if not items:\n        return []\n    k %= len(items)\n    return items[-k:] + items[:-k] if k else list(items)\n",
        "assert solve([1,2,3],1)==[3,1,2]\nassert solve([1,2,3],-1)==[2,3,1]\nassert solve([],5)==[]\nitems=[1]\nassert solve(items,0) is not items\n",
    ),
    (
        "coalesce",
        "train",
        "Devuelve el primer valor distinto de None; conserva 0, False y cadena vacia.",
        "def solve(items):\n    return next((item for item in items if item is not None), None)\n",
        "assert solve([None,0,3])==0\nassert solve([None,False]) is False\nassert solve([None,''])==''\nassert solve([]) is None\n",
    ),
    (
        "median",
        "dev",
        "Calcula la mediana numerica sin mutar la entrada; rechaza una lista vacia.",
        "def solve(items):\n    if not items:\n        raise ValueError('empty input')\n    values = sorted(items)\n    n = len(values)\n    return values[n//2] if n % 2 else (values[n//2-1] + values[n//2])/2\n",
        "items=[3,1,2]\nassert solve(items)==2\nassert items==[3,1,2]\nassert solve([4,1,3,2])==2.5\ntry:\n    solve([])\nexcept ValueError:\n    pass\nelse:\n    raise AssertionError('empty input accepted')\n",
    ),
    (
        "merge-intervals",
        "dev",
        "Une intervalos cerrados solapados o que se toquen; no cambies la entrada.",
        "def solve(intervals):\n    result = []\n    for lo, hi in sorted(intervals):\n        if lo > hi:\n            raise ValueError('invalid interval')\n        if result and lo <= result[-1][1]:\n            result[-1][1] = max(result[-1][1], hi)\n        else:\n            result.append([lo, hi])\n    return result\n",
        "items=[[5,7],[1,3],[3,6]]\nassert solve(items)==[[1,7]]\nassert items==[[5,7],[1,3],[3,6]]\nassert solve([])==[]\nassert solve([[0,1],[3,4]])==[[0,1],[3,4]]\n",
    ),
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a project file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a project file",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shell",
            "description": "Run a command in the project",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]


def call(name, arguments):
    return {
        "role": "assistant",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "arguments": arguments,
                },
            }
        ],
    }


def build(destination):
    destination.mkdir(parents=True, exist_ok=False)
    rows = []
    for family, split, objective, code, checks in CASES:
        with tempfile.TemporaryDirectory(prefix="kali-training-seed-") as folder:
            root = Path(folder)
            starter = "def solve(*args):\n    raise NotImplementedError('pending')\n"
            (root / "solution.py").write_text(starter, encoding="utf-8")
            (root / "check.py").write_text(
                "from solution import solve\n" + checks + "print('CHECK_OK')\n", encoding="utf-8"
            )
            before = subprocess.run(
                [sys.executable, "-B", "check.py"],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            assert before.returncode != 0, family
            (root / "solution.py").write_text(code, encoding="utf-8")
            after = subprocess.run(
                [sys.executable, "-B", "check.py"],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            assert after.returncode == 0, (family, after.stderr)
        rows.append(
            {
                "id": family,
                "family": family,
                "split": split,
                "source": "Original hand-authored seed / nachoweb3 / MIT",
                "model_generated": False,
                "verification": {
                    "before_exit": before.returncode,
                    "after_exit": after.returncode,
                    "checks_sha256": hashlib.sha256(checks.encode()).hexdigest(),
                },
                "tools": TOOLS,
                "messages": [
                    {
                        "role": "system",
                        "content": "Trabaja sobre el proyecto. Inspecciona, implementa y comprueba. No inventes resultados.",
                    },
                    {
                        "role": "user",
                        "content": "Implementa solve en solution.py: "
                        + objective
                        + " Ejecuta check.py.",
                    },
                    call("read_file", {"path": "solution.py"}),
                    {"role": "tool", "name": "read_file", "content": starter},
                    call("shell", {"command": "python -B check.py"}),
                    {
                        "role": "tool",
                        "name": "shell",
                        "content": "exit=1\n" + before.stderr.replace(str(root), "<project>"),
                    },
                    call("write_file", {"path": "solution.py", "content": code}),
                    {"role": "tool", "name": "write_file", "content": "File written"},
                    call("shell", {"command": "python -B check.py"}),
                    {"role": "tool", "name": "shell", "content": "exit=0\n" + after.stdout},
                    {
                        "role": "assistant",
                        "content": "Implementado en solution.py. La comprobacion check.py termina con codigo 0. Solo se han comprobado los casos del proyecto.",
                    },
                ],
            }
        )
    for split in ("train", "dev"):
        content = "".join(
            json.dumps(row, ensure_ascii=False) + "\n" for row in rows if row["split"] == split
        )
        (destination / (split + ".jsonl")).write_text(content, encoding="utf-8")
    manifest = {
        "status": "seed-pipeline-validation-only",
        "counts": {split: sum(r["split"] == split for r in rows) for split in ("train", "dev")},
        "limitations": [
            "Ten tiny hand-authored examples, not a production training corpus",
            "Tool names need adaptation to deployment schema",
            "No held-out model evaluation or measured improvement yet",
        ],
        "sha256": {
            name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
            for name in ("train.jsonl", "dev.jsonl")
        },
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
