"""Execute the workflow's actual run blocks without third-party dependencies."""

import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github/workflows/create-release-pull-request-for-flutter-app.yaml").read_text()


def step(name):
    # Only extract literal run/env blocks at the workflow's step indentation.
    blocks = re.split(r"^      - ", WORKFLOW, flags=re.MULTILINE)
    return next(block for block in blocks if block.startswith(f"name: {name}\n"))


def run_block(block):
    match = re.search(r"^        run: \|\n((?:          [^\n]*\n|\n)+)", block, re.MULTILINE)
    if match:
        return textwrap.dedent(match[1])
    return re.search(r"^        run: ([^\n]+)", block, re.MULTILINE)[1]


def render(value, context):
    return re.sub(r"\$\{\{\s*(.*?)\s*\}\}", lambda match: context[match[1]], value)


VALIDATION = step("Validate build number and set version and branch to GITHUB_OUTPUT")


class ReleaseBuildNumberTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, GITHUB_ENV=str(self.root / "env"), GITHUB_OUTPUT=str(self.root / "output"))

    def execute(self, block, context, cwd=None):
        env = self.env.copy()
        context = context.copy()
        match = re.search(r"^        env:\n((?:          [^\n]*\n)+)", block, re.MULTILINE)
        if match:
            for line in textwrap.dedent(match[1]).splitlines():
                key, value = line.split(": ", 1)
                if value.startswith('"') and value.endswith('"'):
                    value = json.loads(value)
                env[key] = render(value, context)
                context[f"env.{key}"] = env[key]
        return subprocess.run(
            ["bash", "-e", "-c", render(run_block(block), context)],
            env=env, cwd=cwd or self.root, text=True, capture_output=True,
        )

    def resolve(self, requested=None, version="", segment="", directory="./", current="670"):
        for output_file in ("GITHUB_ENV", "GITHUB_OUTPUT"):
            Path(self.env[output_file]).unlink(missing_ok=True)
        context = {
            "inputs.version": version,
            "inputs.build-number": requested or "",
            "inputs.branch-path-segment": segment,
            "inputs.working-directory": directory,
            "steps.pubspec.outputs.version-number": "2.76.0",
            "steps.pubspec.outputs.build-number": current,
        }
        version_step = "Set input version to GITHUB_ENV" if version else "Set current version to GITHUB_ENV"
        for name in (version_step, "Set branch name to GITHUB_OUTPUT"):
            result = self.execute(step(name), context)
            self.assertEqual(result.returncode, 0, result.stderr)
            for line in Path(self.env["GITHUB_ENV"]).read_text().splitlines():
                key, value = line.split("=", 1)
                context[f"env.{key}"] = value
        result = self.execute(VALIDATION, context)
        output = Path(self.env["GITHUB_OUTPUT"])
        values = dict(line.split("=", 1) for line in output.read_text().splitlines()) if output.exists() else {}
        return result, values

    def test_default_and_explicit_numbers_with_existing_inputs(self):
        for requested, version, segment, directory in itertools.product(
            (None, "", "672"), ("", "2.76.1"), ("", "client"), ("./", "./packages/flutter_app")
        ):
            with self.subTest(requested=requested, version=version, segment=segment, directory=directory):
                result, values = self.resolve(requested, version, segment, directory)
                self.assertEqual(result.returncode, 0, result.stderr)
                expected_version = version or "2.76.0"
                expected_branch = f"release/{segment + '/' if segment else ''}{expected_version}"
                self.assertEqual(values, {
                    "version": expected_version,
                    "build-number": "672" if requested else "671",
                    "branch": expected_branch,
                })

    def test_invalid_numbers_fail_without_outputs_or_shell_execution(self):
        marker = self.root / "injected"
        for requested, reason in (
            ("670", "greater than the current"), ("669", "greater than the current"),
            ("0", "greater than 0"), ("-1", "positive integer"),
            ("671.5", "only digits"), ("abc", "only digits"),
            (" 672", "only digits"), ("672\n", "only digits"),
            ("+672", "only digits"), ("６７２", "only digits"),
            (f"$(touch {marker})", "only digits"),
            (f'672"; touch {marker}; #', "only digits"),
        ):
            with self.subTest(requested=requested):
                result, values = self.resolve(requested)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("::error::", result.stderr)
                self.assertIn(reason, result.stderr)
                self.assertEqual(values, {})
                self.assertFalse(marker.exists())

    def test_decimal_normalization_and_large_numbers(self):
        for requested, expected in (("000672", "672"), ("9223372036854775808", "9223372036854775808")):
            with self.subTest(requested=requested):
                result, values = self.resolve(requested)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(values["build-number"], expected)
        result, values = self.resolve(current="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(values["build-number"], "1")

    def test_validation_precedes_remote_mutations(self):
        self.assertNotIn("${{", run_block(VALIDATION))
        self.assertRegex(VALIDATION, r"REQUESTED_BUILD_NUMBER: \$\{\{ inputs.build-number \}\}")
        for job, dependencies in (
            ("create-branch", "set-version-and-branch"),
            ("bump-version", "set-version-and-branch, create-branch"),
            ("create-pr", "set-version-and-branch, bump-version"),
        ):
            self.assertRegex(WORKFLOW, rf"(?s)\n  {job}:\n.*?    needs: \[{dependencies}\]")
        first_job = WORKFLOW.split("\n  create-branch:")[0]
        self.assertNotRegex(first_job, r"git (?:switch|push)|gh pr create")

    def test_pubspec_commit_and_pr_use_the_same_resolved_number(self):
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        log = self.root / "commands.jsonl"
        for command in ("git", "gh"):
            shim = bin_dir / command
            shim.write_text(
                f"#!{sys.executable}\nimport json, sys\n"
                f"with open({str(log)!r}, 'a') as output:\n"
                "    output.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            )
            shim.chmod(0o755)
        self.env["PATH"] = f"{bin_dir}{os.pathsep}{self.env['PATH']}"
        self.env.update(GITHUB_REF="main", GITHUB_ACTOR="tester", GITHUB_TOKEN="test-token")
        for requested, version, segment, directory in itertools.product(
            (None, "", "672"), ("", "2.76.1"), ("", "client"), ("./", "./packages/flutter_app")
        ):
            with self.subTest(requested=requested, version=version, segment=segment, directory=directory):
                result, values = self.resolve(requested, version, segment, directory)
                self.assertEqual(result.returncode, 0, result.stderr)
                context = {f"env.{key}": value for key, value in values.items()}
                context["steps.generate_token.outputs.token"] = "test-token"
                app_dir = self.root / directory
                app_dir.mkdir(parents=True, exist_ok=True)
                pubspec = app_dir / "pubspec.yaml"
                pubspec.write_text("name: flutter_app\nversion: 2.76.0+670\n")
                bump = step("Bump version and build number")
                # macOS sed requires an explicit empty backup suffix for -i.
                if sys.platform == "darwin":
                    bump = bump.replace("sed -i ", "sed -i '' ")
                result = self.execute(bump, context, cwd=app_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                release = f"{values['version']}+{values['build-number']}"
                self.assertIn(f"version: {release}\n", pubspec.read_text())
                for name in ("Commit & Push", "Create release PR"):
                    result = self.execute(step(name), context)
                    self.assertEqual(result.returncode, 0, result.stderr)
                commands = [json.loads(line) for line in log.read_text().splitlines()]
                self.assertEqual(commands[-3], ["commit", "-m", f"build: bump app to {release}"])
                self.assertEqual(commands[-2], ["push", "origin", values["branch"]])
                self.assertEqual(commands[-1][commands[-1].index("-t") + 1], f"build: bump app to {release}")


if __name__ == "__main__":
    unittest.main()
