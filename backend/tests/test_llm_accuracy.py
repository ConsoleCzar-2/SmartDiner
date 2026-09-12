import json
import os
import pytest
import asyncio
from app.services.constraint_extractor import extract_constraints

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "golden_test_cases.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "TEST_REPORT_ACCURACY.md")

def load_golden_cases():
    with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_case(case: dict, extracted) -> dict:
    expected = case["expected"]
    field_results = {}
    passed = True

    # 1. People count
    if "people_count" in expected:
        match = extracted.people_count == expected["people_count"]
        field_results["people_count"] = {"match": match, "exp": expected["people_count"], "act": extracted.people_count}
        if not match: passed = False

    # 2. Max budget
    if "max_budget" in expected:
        act_b = float(extracted.max_budget) if extracted.max_budget is not None else None
        exp_b = float(expected["max_budget"])
        match = act_b is not None and abs(act_b - exp_b) <= (exp_b * 0.05)
        field_results["max_budget"] = {"match": match, "exp": exp_b, "act": act_b}
        if not match: passed = False

    # 3. Vegetarian count
    if "vegetarian_count" in expected:
        match = (extracted.vegetarian_count or 0) == expected["vegetarian_count"]
        field_results["vegetarian_count"] = {"match": match, "exp": expected["vegetarian_count"], "act": extracted.vegetarian_count}
        if not match: passed = False

    # 4. Non-vegetarian count
    if "non_vegetarian_count" in expected:
        act_nv = extracted.non_vegetarian_count
        if act_nv is None and extracted.people_count:
            act_nv = max(0, extracted.people_count - (extracted.vegetarian_count or 0) - (extracted.vegan_count or 0))
        match = (act_nv or 0) == expected["non_vegetarian_count"]
        field_results["non_vegetarian_count"] = {"match": match, "exp": expected["non_vegetarian_count"], "act": act_nv}
        if not match: passed = False

    # 5. Vegan count
    if "vegan_count" in expected:
        match = (extracted.vegan_count or 0) == expected["vegan_count"]
        field_results["vegan_count"] = {"match": match, "exp": expected["vegan_count"], "act": extracted.vegan_count}
        if not match: passed = False

    # 6. Spice level
    if "max_spice_level" in expected:
        match = extracted.max_spice_level == expected["max_spice_level"]
        field_results["max_spice_level"] = {"match": match, "exp": expected["max_spice_level"], "act": extracted.max_spice_level}
        if not match: passed = False

    # 7. Excluded allergens
    if "excluded_allergens" in expected:
        act_algs = set(a.lower() for a in (extracted.excluded_allergens or []))
        exp_algs = set(a.lower() for a in expected["excluded_allergens"])
        match = exp_algs.issubset(act_algs)
        field_results["excluded_allergens"] = {"match": match, "exp": list(exp_algs), "act": list(act_algs)}
        if not match: passed = False

    # 8. Specific dishes
    if "specific_dish_requests" in expected:
        act_dishes = " ".join(extracted.specific_dish_requests or []).lower()
        match = all(d.lower() in act_dishes for d in expected["specific_dish_requests"])
        field_results["specific_dish_requests"] = {"match": match, "exp": expected["specific_dish_requests"], "act": extracted.specific_dish_requests}
        if not match: passed = False

    return {
        "id": case["id"],
        "category": case.get("category", "General"),
        "input": case["input_message"],
        "passed": passed,
        "fields": field_results
    }

async def extract_with_retry(input_message: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await extract_constraints(input_message)
        except Exception as e:
            err_str = str(e).lower()
            if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                wait_time = 15.0 * (attempt + 1)
                print(f"[RateLimit] 429 hit. Backing off for {wait_time}s (attempt {attempt+1}/{max_retries})...")
                await asyncio.sleep(wait_time)
            else:
                raise e
    return await extract_constraints(input_message)

@pytest.mark.asyncio
async def test_golden_suite_accuracy():
    """
    Executes the Golden Test Suite and validates constraint extraction accuracy >= 85%.
    Paces requests to respect Gemini 15 RPM rate limits.
    """
    all_cases = load_golden_cases()
    # By default evaluate 15 representative cases spanning all categories to stay within standard test budgets
    # Set FULL_BENCHMARK=1 in environment to run all 50 cases
    run_all = os.environ.get("FULL_BENCHMARK", "0") == "1"
    if run_all:
        cases = all_cases
    else:
        # Sample 15 diverse cases across all categories
        selected_indices = [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 43, 46, 48, 49]
        cases = [all_cases[i] for i in selected_indices if i < len(all_cases)]

    results = []

    for idx, case in enumerate(cases):
        safe_preview = case["input_message"][:40].encode("ascii", "replace").decode("ascii")
        print(f"[{idx+1}/{len(cases)}] Testing Case {case['id']}: {safe_preview}...")
        try:
            ext_obj, _ = await extract_with_retry(case["input_message"])
            results.append(evaluate_case(case, ext_obj))
        except Exception as err:
            results.append({
                "id": case["id"],
                "category": case.get("category", "General"),
                "input": case["input_message"],
                "passed": False,
                "fields": {"error": str(err)}
            })
        # Pace at ~4.2s per call to strictly adhere to 15 RPM limit
        if idx < len(cases) - 1:
            await asyncio.sleep(4.2)

    # Calculate statistics
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    accuracy_pct = round((passed_count / total) * 100, 1)

    # Category breakdown
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    # Generate Markdown Report
    report_lines = [
        "# SmartDiner LLM Constraint Extraction — Golden Test Suite Accuracy Report",
        "",
        "## Summary Metrics",
        f"- **Total Golden Test Cases:** {total}",
        f"- **Passed Cases:** {passed_count}",
        f"- **Failed Cases:** {total - passed_count}",
        f"- **Overall Extraction Accuracy:** {accuracy_pct}%",
        f"- **Pass Threshold:** 85.0%",
        f"- **Status:** {'PASSED' if accuracy_pct >= 85.0 else 'FAILED'}",
        "",
        "## Accuracy Breakdown by Category",
        "| Category | Cases | Passed | Accuracy (%) |",
        "|---|---|---|---|"
    ]

    for cat, stats in sorted(categories.items()):
        cat_pct = round((stats["passed"] / stats["total"]) * 100, 1)
        report_lines.append(f"| {cat} | {stats['total']} | {stats['passed']} | {cat_pct}% |")

    report_lines.extend([
        "",
        "## Detailed Case Results",
        "| ID | Category | Status | Input Message | Failure Details |",
        "|---|---|---|---|---|"
    ])

    for r in results:
        status_str = "PASS" if r["passed"] else "FAIL"
        failed_fields = []
        if not r["passed"]:
            for fname, fval in r["fields"].items():
                if isinstance(fval, dict) and not fval.get("match", True):
                    failed_fields.append(f"{fname} (exp: {fval.get('exp')}, act: {fval.get('act')})")
                elif fname == "error":
                    failed_fields.append(fval)
        failure_str = "; ".join(failed_fields) if failed_fields else "-"
        # Sanitize pipe characters in message
        clean_msg = r["input"].replace("|", "/")
        report_lines.append(f"| {r['id']} | {r['category']} | {status_str} | {clean_msg} | {failure_str} |")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\n[Golden Suite] Accuracy: {passed_count}/{total} ({accuracy_pct}%). Report saved to {REPORT_PATH}")
    assert accuracy_pct >= 85.0, f"Accuracy {accuracy_pct}% is below required 85.0% threshold."
