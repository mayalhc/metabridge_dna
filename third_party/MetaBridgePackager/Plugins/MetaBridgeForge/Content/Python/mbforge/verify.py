"""Wraps unreal.VerifyMetaHumanOutfitClothing - the scriptable equivalent
of MetaHuman Manager's Verify button.

NOTE: unreal.MetaHumanAssetReport's exact editor-property layout wasn't
confirmed against a live console during scoping (only the verifier class
itself - VerifyMetaHumanOutfitClothing.verify(to_verify, report, options) -
was confirmed to exist). format_report() below tries several plausible
property names defensively and falls back to the report's own repr if none
of them exist, so this still produces *something* useful the first time
it's run - but the report text may need a follow-up pass once the real
property names are known (run `print([p for p in dir(report) if not
p.startswith('_')])` in the console after a real verify() call to find them
if the fallback repr isn't readable enough).
"""
import unreal


def _try_report_text(report) -> str:
    # Most likely shapes for a Fab-style asset verification report:
    # a list of message/severity structs under one of these names.
    for prop_name in ("messages", "entries", "results", "issues"):
        try:
            entries = report.get_editor_property(prop_name)
        except Exception:
            continue
        if entries is None:
            continue
        lines = []
        for e in entries:
            lines.append(str(e))
        if lines:
            return "\n".join(lines)
        return f"(no {prop_name} - report is clean)"

    # Some verification reports expose a simple pass/fail flag.
    for prop_name in ("has_errors", "has_issues", "passed", "success"):
        try:
            return f"{prop_name} = {report.get_editor_property(prop_name)}"
        except Exception:
            continue

    return str(report)


def run_verification(asset) -> tuple[bool, str]:
    """Runs VerifyMetaHumanOutfitClothing against `asset` (the OA_ Outfit
    Asset). Returns (looks_ok, report_text). looks_ok is a best-effort
    guess (True unless the report text obviously mentions an error/failure
    keyword) - always read report_text, don't rely on looks_ok alone until
    the real report structure has been confirmed.
    """
    verifier = unreal.VerifyMetaHumanOutfitClothing()
    report = unreal.MetaHumanAssetReport()
    options = unreal.MetaHumanVerificationOptions()

    try:
        verifier.verify(asset, report, options)
    except Exception as e:
        return False, f"verify() raised an exception: {e}"

    text = _try_report_text(report)
    looks_ok = not any(
        kw in text.lower() for kw in ("error", "fail", "invalid")
    )
    return looks_ok, text
