"""Real Docker integration checks. Pull the named image explicitly first."""

import os
from pathlib import Path
import tempfile

from kali_agente.sandbox import run


def main():
    with tempfile.TemporaryDirectory(prefix="kali-sandbox-") as folder:
        root = Path(folder)
        (root / "input.txt").write_text("original")
        os.environ["KALI_SANDBOX_SECRET_FIXTURE"] = "must-not-reach-container"
        common = ["--imagen", "python:3.13-alpine", "--carpeta", folder]
        program = """import os
from pathlib import Path
assert Path('/workspace/input.txt').read_text() == 'original'
assert 'KALI_SANDBOX_SECRET_FIXTURE' not in os.environ
assert not Path('/var/run/docker.sock').exists()
assert sorted(p.name for p in Path('/sys/class/net').iterdir()) == ['lo']
for name in ('/workspace/input.txt', '/usr/forbidden'):
    try:
        Path(name).write_text('forbidden')
    except OSError:
        pass
    else:
        raise AssertionError('Unexpected write: ' + name)
print('Docker: read-only project/root, no network, no host secrets/socket OK')
"""
        assert run([*common, "--", "python", "-c", program]) == 0
        assert (root / "input.txt").read_text() == "original"
        assert (
            run(
                [
                    *common,
                    "--escribir",
                    "--",
                    "python",
                    "-c",
                    "from pathlib import Path; Path('/workspace/new.txt').write_text('ok')",
                ]
            )
            == 0
        )
        assert (root / "new.txt").read_text() == "ok"
        assert (
            run([*common, "--segundos", "1", "--", "python", "-c", "import time; time.sleep(30)"])
            == 124
        )
        print("Docker: explicit writes and timeout cleanup OK")


if __name__ == "__main__":
    main()
