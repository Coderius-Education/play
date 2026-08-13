"""Scoped mutation testing: does the suite actually notice broken code?

Coverage says a line ran. It does not say anything would have failed had that
line been wrong. This changes one thing in the source, runs a chosen slice of
the suite, and reports every change nothing complained about. Each survivor is
a place where the code could be wrong today and stay green.

    python tools/mutation_check.py play/callback/collision_callbacks.py \\
        --tests tests/physics_collisions --limit 40

Scoped on purpose: one mutant costs a full run of the chosen tests, so point it
at one module and the fastest tests that cover it rather than the whole suite.

Exit status is 1 when any mutant survives, so this can gate CI once a module is
clean.
"""

import argparse
import ast
import copy
import pathlib
import subprocess
import sys
import time

# Test outcome is read from pytest's own summary, not the exit code: some
# modules in this project segfault at interpreter shutdown *after* reporting
# every test as passed, and that exit status would otherwise be scored as the
# mutant having been caught.
PASS_MARKER = " passed"
FAIL_MARKERS = (" failed", " error", "errors")


class _Mutator(ast.NodeTransformer):
    """Applies exactly one mutation, the *target*-th opportunity it finds."""

    COMPARISONS = {
        ast.Eq: ast.NotEq,
        ast.NotEq: ast.Eq,
        ast.Lt: ast.GtE,
        ast.GtE: ast.Lt,
        ast.Gt: ast.LtE,
        ast.LtE: ast.Gt,
        ast.Is: ast.IsNot,
        ast.IsNot: ast.Is,
        ast.In: ast.NotIn,
        ast.NotIn: ast.In,
    }

    def __init__(self, target):
        self.target = target
        self.seen = 0
        self.description = None

    def _hit(self, node, description):
        """Return True if this is the opportunity we were asked to mutate."""
        self.seen += 1
        if self.seen - 1 == self.target:
            self.description = f"line {getattr(node, 'lineno', '?')}: {description}"
            return True
        return False

    def visit_Compare(self, node):
        self.generic_visit(node)
        for i, op in enumerate(node.ops):
            replacement = self.COMPARISONS.get(type(op))
            if replacement is None:
                continue
            if self._hit(node, f"{type(op).__name__} -> {replacement.__name__}"):
                node.ops[i] = replacement()
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        flipped = ast.Or if isinstance(node.op, ast.And) else ast.And
        if self._hit(node, f"{type(node.op).__name__} -> {flipped.__name__}"):
            node.op = flipped()
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.Not) and self._hit(node, "drop `not`"):
            return node.operand
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            if self._hit(node, f"{node.value} -> {not node.value}"):
                return ast.Constant(value=not node.value)
        elif isinstance(node.value, int) and node.value in (0, 1):
            if self._hit(node, f"{node.value} -> {1 - node.value}"):
                return ast.Constant(value=1 - node.value)
        return node


def count_opportunities(tree):
    counter = _Mutator(target=-1)
    counter.visit(copy.deepcopy(tree))
    return counter.seen


def run_tests(command, timeout):
    """Return (verdict, summary) where verdict is killed/survived/inconclusive.

    Reads pytest's summary line, not exit status. Unparseable output is
    reported as inconclusive rather than assumed killed: this tool exists to
    find places the tests do not constrain, so a failure to measure must never
    be reported as a success. An earlier version returned "killed" here, and a
    stray second -q — which makes pytest drop the summary line — turned ten
    unmeasured mutants into ten apparent passes.
    """
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        # A mutant that hangs is a mutant the tests noticed, in the sense that
        # matters: the suite did not sail past it.
        return "killed", "timed out"

    output = proc.stdout + proc.stderr
    summary = ""
    for line in output.splitlines():
        if PASS_MARKER in line or any(m in line for m in FAIL_MARKERS):
            summary = line.strip()
    if any(marker in output for marker in FAIL_MARKERS):
        return "killed", summary or "failed"
    if PASS_MARKER in output:
        return "survived", summary or "passed"
    return "inconclusive", summary or "no pytest summary found in output"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="python file to mutate")
    parser.add_argument("--tests", required=True, help="tests to run per mutant")
    parser.add_argument("--limit", type=int, default=40, help="max mutants")
    parser.add_argument(
        "--only",
        help=(
            "comma-separated mutant indices to run. Use it to re-check the "
            "survivors of a fast slice against the whole suite: a survivor "
            "only ever means the tests that ran did not constrain it"
        ),
    )
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()

    path = pathlib.Path(args.target)
    original = path.read_text()
    tree = ast.parse(original)
    total = count_opportunities(tree)
    planned = min(total, args.limit)

    if args.only:
        indices = [int(part) for part in args.only.split(",") if part.strip()]
        planned = len(indices)
    else:
        indices = range(planned)

    command = f"python -m pytest {args.tests} -q -p no:randomly"
    print(f"{path}: {total} mutation opportunities, running {planned}")
    print(f"per-mutant command: {command}\n")

    survivors = []
    inconclusive = []
    started = time.time()
    try:
        for index in indices:
            mutator = _Mutator(target=index)
            mutated = mutator.visit(copy.deepcopy(tree))
            if mutator.description is None:
                continue
            ast.fix_missing_locations(mutated)
            try:
                source = ast.unparse(mutated)
            except Exception as exc:  # pragma: no cover - defensive
                print(f"  [{index}] skipped, could not unparse: {exc}")
                continue

            path.write_text(source)
            verdict, summary = run_tests(command, args.timeout)
            label = {
                "killed": "killed  ",
                "survived": "SURVIVED",
                "inconclusive": "?UNKNOWN",
            }[verdict]
            print(f"  [{index:>3}] {label}  {mutator.description}  ({summary})")
            if verdict == "survived":
                survivors.append(mutator.description)
            elif verdict == "inconclusive":
                inconclusive.append(f"{mutator.description} ({summary})")
    finally:
        path.write_text(original)

    elapsed = time.time() - started
    print(f"\n{len(survivors)} survived of {planned} in {elapsed:.0f}s")
    for description in survivors:
        print(f"  SURVIVED  {description}")
    if inconclusive:
        print(f"\n{len(inconclusive)} could not be measured — fix these first:")
        for description in inconclusive:
            print(f"  ?UNKNOWN  {description}")
        print("  (a common cause is passing -q in --tests: pytest then drops")
        print("   the summary line this tool reads)")
    return 1 if survivors or inconclusive else 0


if __name__ == "__main__":
    sys.exit(main())
