"""
Record the exact environment a run was made in.

Writes results/environment.txt, which is committed alongside the results so that
anyone can see what produced them.

    python record_environment.py
"""
from __future__ import annotations

import datetime
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "environment.txt")


def pip_freeze(python_exe: str) -> str:
    try:
        out = subprocess.run([python_exe, "-m", "pip", "freeze"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return out.stdout.decode("utf-8", "replace").strip() or "(no packages reported)"
    except Exception as exc:                       # pragma: no cover
        return f"(pip freeze failed: {exc})"


def main() -> None:
    import numpy
    import pandas

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    now_local = datetime.datetime.now()
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    lines = [
        "Environment record for this run",
        "=" * 60,
        "",
        "Recorded (local) : %s" % now_local.strftime("%Y-%m-%d %H:%M:%S"),
        "Recorded (UTC)   : %s" % now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "",
        "Operating system : %s %s" % (platform.system(), platform.release()),
        "Machine          : %s" % platform.machine(),
        "Processor        : %s" % (platform.processor() or "(not reported)"),
        "",
        "Python           : %s" % sys.version.replace("\n", " "),
        "Python executable: %s" % sys.executable,
        "Byte order       : %s" % sys.byteorder,
        "",
        "numpy            : %s" % numpy.__version__,
        "pandas           : %s" % pandas.__version__,
        "",
        "Command used     : python run_experiments.py",
        "",
        "-" * 60,
        "pip freeze",
        "-" * 60,
        pip_freeze(sys.executable),
        "",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
