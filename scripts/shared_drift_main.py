from __future__ import annotations

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main", help="sibling branch to compare against")
    parser.add_argument("--src", default=f"src/{OUR_PACKAGE}", help="our package root")
    parser.add_argument(
        "--no-pair",
        action="store_true",
        help="always compare against --ref, never a sibling branch of the same name",
    )
    args = parser.parse_args()
    ours = Path(args.src)
    workspace = Path(tempfile.mkdtemp(prefix="drift-"))
    compared_against = args.ref
    try:
        theirs, compared_against = clone_sibling(
            workspace / "sibling", args.ref, prefer=None if args.no_pair else current_branch()
        )
        problems = compare(ours, theirs)
        stray = unlisted(ours)
    except subprocess.CalledProcessError as exc:
        print(f"could not clone {SIBLING_URL}: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
    if stray:
        print("modules in neither SHARED nor DIVERGENT (add them to the manifest):")
        for name in stray:
            print(f"  {name}")
    if problems:
        print(f"\nshared modules out of lockstep with {SIBLING_URL}@{compared_against}:")
        for problem in problems:
            print(f"  {problem}")
        print(
            "\nThe two agents duplicate this logic deliberately — sharing a live-state\n"
            "module disqualifies the solution — so a change to one must land in both."
        )
    if problems or stray:
        return 1
    print(f"{len(SHARED)} shared modules in lockstep with {SIBLING_URL}@{compared_against}")
    return 0

def normalise(text: str) -> str:
    return _PACKAGE_RE.sub("AGENT", text)
def unlisted(ours: Path) -> list[str]:
    known = set(SHARED) | set(DIVERGENT)
    found = {str(p.relative_to(ours)) for p in ours.rglob("*.py")}
    return sorted(f for f in found - known if not f.endswith("__init__.py"))

def install(namespace: dict[str, object]) -> None:
    globals().update(namespace)
