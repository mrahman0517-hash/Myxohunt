"""
web/build.py — copy the simulation's Python files that the web app needs into web/py/ and list
them in web/py/manifest.json (B94). Run it after changing the simulation, before deploying:

    python web/build.py [--head]     (--head: core files from the last commit)

Only the engine, its settings catalogue and web_controller.py go to the browser; the pygame app,
the recorder and the check scripts stay out.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "predation-sim")
OUT = os.path.join(HERE, "py")
FILES = ["app_params.py", "colonies.py", "contacts.py", "counters.py", "ecoli_body.py", "ecoli_life.py", "engine.py",
         "fields_update.py", "geometry.py", "grids.py", "myxo_alignment.py", "myxo_body.py", "myxo_energy.py",
         "myxo_famine.py", "myxo_modes.py", "myxo_reversals.py", "predation.py", "seeding.py", "settings.py",
         "state.py", "stats.py", "web_controller.py"]


def main():
    """Copy the files and write the manifest."""
    os.makedirs(OUT, exist_ok=True)
    head = "--head" in sys.argv          # core files as last committed (another session may be editing them)
    for name in FILES:
        if head and name != "web_controller.py":
            text = subprocess.run(["git", "show", f"HEAD:predation-sim/{name}"], cwd=HERE, capture_output=True,
                                  check=True).stdout
            with open(os.path.join(OUT, name), "wb") as fh:
                fh.write(text)
        else:
            shutil.copy2(os.path.join(SRC, name), os.path.join(OUT, name))
    scenes = sorted(f for f in os.listdir(os.path.join(HERE, "scenes")) if f.endswith(".pkl.gz"))         if os.path.isdir(os.path.join(HERE, "scenes")) else []
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf8") as fh:
        json.dump(dict(files=FILES, scenes=scenes), fh, indent=1)
    print(f"copied {len(FILES)} files to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
