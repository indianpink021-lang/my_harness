#!/usr/bin/env python3
"""허들링 하네스 판정기 (읽기 전용).

사용법:
  python3 harness/judge.py <G1|G2|G3|S5> runs/<screen>
  python3 harness/judge.py --selftest

규칙은 harness/rules.json(SSOT)에서만 읽는다. 결과 JSON은 stdout으로만 출력하고 파일을 쓰지 않는다.
종료 코드: 0 = pass, 1 = fail, 2 = 사용법/입력 오류.
"""
import copy
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RULES_PATH = os.path.join(HERE, "rules.json")
FIXTURES = os.path.join(HERE, "tests", "fixtures")


def load_rules():
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------- 파일 읽기 ----------

def read_text(run_dir, rel):
    path = os.path.join(run_dir, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def read_json(run_dir, rel):
    text = read_text(run_dir, rel)
    return None if text is None else json.loads(text)


def as_items(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return data["items"]
    return []


# ---------- Markdown ----------

HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
ITEM = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.*)$")
URL = re.compile(r"https?://[^\s)>\]`]+")


def sections(md):
    out, cur = {}, None
    for line in md.splitlines():
        m = HEADING.match(line)
        if m:
            cur = m.group(1).strip()
            out.setdefault(cur, [])
        elif cur is not None:
            out[cur].append(line)
    return out


def items(lines):
    return [m.group(1) for m in (ITEM.match(l) for l in lines) if m]


def norm_line(line):
    s = line.strip()
    s = re.sub(r"^(?:[-*]|\d+\.)\s+", "", s)
    return s.replace("`", "").strip()


# ---------- Figma JSON ----------

def all_nodes(export):
    for frame in export.get("frames", []):
        for node in frame.get("nodes", []):
            yield frame, node


def norm_color(c):
    return re.sub(r"\s+", "", str(c)).lower()


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


# ---------- 규칙 판정 ----------

def check(rule, run_dir, screen, rules):
    """(pass: bool, detail: str) 반환."""
    c = rule["check"]
    applies = rule.get("when_screen_in")
    if applies is not None and screen not in applies:
        return True, "n/a (대상 화면 아님)"

    # --- JSON 목록 ---
    if c in ("count_items", "all_have_field"):
        data = read_json(run_dir, rule["file"])
        if data is None:
            return False, f"파일 없음: {rule['file']}"
        its = as_items(data)
        if c == "count_items":
            return compare(len(its), rule["op"], rule["value"]), f"항목 수 {len(its)}"
        missing = [i for i, it in enumerate(its) if not (isinstance(it, dict) and it.get(rule["field"]))]
        return not missing, f"{rule['field']} 없는 항목 index {missing}" if missing else "ok"

    # --- Markdown ---
    if c in ("has_sections", "count_items_in_section", "urls_subset_of",
             "section_contains_any", "section_contains_line", "sale_requested_roles_equal"):
        md = read_text(run_dir, rule["file"])
        if md is None:
            return False, f"파일 없음: {rule['file']}"
        secs = sections(md)
        if c == "has_sections":
            miss = [s for s in rule["sections"] if s not in secs]
            return not miss, f"없는 섹션 {miss}" if miss else "ok"
        sec = secs.get(rule["section"])
        if sec is None:
            return False, f"섹션 없음: {rule['section']}"
        if c == "count_items_in_section":
            n = len(items(sec))
            return compare(n, rule["op"], rule["value"]), f"항목 수 {n}"
        if c == "urls_subset_of":
            src_file, field = rule["of"].split(":")
            src = read_json(run_dir, src_file)
            if src is None:
                return False, f"파일 없음: {src_file}"
            allowed = {it.get(field) for it in as_items(src) if isinstance(it, dict)}
            used = URL.findall("\n".join(sec))
            bad = [u for u in used if u not in allowed]
            return not bad, f"레퍼런스에 없는 URL {bad}" if bad else f"URL {len(used)}개 확인"
        text = "\n".join(sec)
        if c == "section_contains_any":
            hit = [v for v in rule["values"] if re.search(rf"\b{re.escape(v)}\b", text)]
            return bool(hit), f"발견 {hit}" if hit else "역할 없음"
        lines = [norm_line(l) for l in sec]
        if c == "section_contains_line":
            return rule["line"] in lines, "ok" if rule["line"] in lines else f"'{rule['line']}' 줄 없음"
        if c == "sale_requested_roles_equal":
            found = [l for l in lines if l.startswith("sale_requested:")]
            if not found:
                return False, "'sale_requested:' 줄 없음"
            roles = sorted(r for r in re.split(r"[,\s]+", found[0].split(":", 1)[1]) if r)
            ok = roles == sorted(rule["roles"])
            return ok, f"sale_requested 역할 {roles}"

    # --- 승인 기록 ---
    if c == "header_lines":
        md = read_text(run_dir, rule["file"])
        if md is None:
            return False, f"파일 없음: {rule['file']}"
        head = {}
        for line in [l for l in md.splitlines() if l.strip()][:10]:
            if ":" in line:
                k, v = line.split(":", 1)
                head.setdefault(k.strip(), v.strip())
        bad = [k for k, pat in rule["lines"].items() if not re.search(pat, head.get(k, ""))]
        return not bad, f"누락/형식 오류 {bad}" if bad else "ok"

    # --- Figma JSON (S5) ---
    export = read_json(run_dir, rules["gates"]["S5_input"])
    if export is None:
        return False, f"파일 없음: {rules['gates']['S5_input']}"
    nodes = list(all_nodes(export))
    fonts = [(n["name"], n["font"]) for _, n in nodes if isinstance(n.get("font"), dict)]

    if c == "colors_in":
        allowed = {norm_color(v) for v in rule["values"]}
        bad = [(n["name"], col) for _, n in nodes
               for col in as_list(n.get("fills")) + as_list(n.get("strokes"))
               if norm_color(col) not in allowed]
        return not bad, f"허용 밖 색 {bad}" if bad else "ok"
    if c == "count_color_per_frame":
        col = norm_color(rule["color"])
        over = []
        for frame in export.get("frames", []):
            k = sum(1 for n in frame.get("nodes", []) if col in map(norm_color, as_list(n.get("fills"))))
            if not compare(k, rule["op"], rule["value"]):
                over.append((frame.get("name"), k))
        return not over, f"초과 프레임 {over}" if over else "ok"
    if c in ("count_color_on_component", "count_border_on_component"):
        hits = [n["name"] for _, n in nodes if n.get("component") == rule["component"] and (
            norm_color(rule["color"]) in map(norm_color, as_list(n.get("fills")))
            if c == "count_color_on_component" else bool(as_list(n.get("strokes"))))]
        return compare(len(hits), rule["op"], rule["value"]), f"{len(hits)}건 {hits}"
    if c == "radius_in":
        exc = rule.get("except", {})
        bad = []
        for _, n in nodes:
            r = n.get("radius")
            if r is None:
                continue
            if n.get("component") in exc:
                if r != exc[n["component"]]:
                    bad.append((n["name"], r))
            elif r not in rule["values"]:
                bad.append((n["name"], r))
        return not bad, f"허용 밖 radius {bad}" if bad else "ok"
    if c == "count_shadows":
        exc = set(rule.get("except_components", []))
        hits = [n["name"] for _, n in nodes if n.get("component") not in exc for _ in as_list(n.get("shadows"))]
        return compare(len(hits), rule["op"], rule["value"]), f"shadow {len(hits)}건 {hits}"
    if c in ("font_family_in", "font_weight_in", "font_size_in"):
        key = {"font_family_in": "family", "font_weight_in": "weight", "font_size_in": "size"}[c]
        bad = [(name, f.get(key)) for name, f in fonts if f.get(key) not in rule["values"]]
        return not bad, f"허용 밖 {key} {bad}" if bad else "ok"
    if c == "letter_spacing_equal":
        bad = [(name, f.get("letterSpacing")) for name, f in fonts if f.get("letterSpacing", 0) != rule["value"]]
        return not bad, f"letterSpacing {bad}" if bad else "ok"
    if c == "count_text_case":
        hits = [name for name, f in fonts if f.get("textCase") == rule["case"]]
        return compare(len(hits), rule["op"], rule["value"]), f"{rule['case']} {len(hits)}건 {hits}"
    if c == "spacing_in":
        # 0 / 미지정은 "간격 없음"으로 보고 검사하지 않는다.
        bad = [(n["name"], k, v) for _, n in nodes for k in ("gap", "padding")
               for v in as_list(n.get(k)) if v not in (0, None) and v not in rule["values"]]
        return not bad, f"허용 밖 간격 {bad}" if bad else "ok"
    if c == "frame_size":
        bad = [(f.get("name"), f.get("width"), f.get("height")) for f in export.get("frames", [])
               if (f.get("width"), f.get("height")) != (rule["width"], rule["height"])]
        return not bad, f"크기 불일치 {bad}" if bad else "ok"
    if c == "max_columns":
        bad = [(f.get("name"), f.get("columns")) for f in export.get("frames", [])
               if not compare(f.get("columns", 1), rule["op"], rule["value"])]
        return not bad, f"컬럼 초과 {bad}" if bad else "ok"
    if c == "component_default_value":
        found = [n for _, n in nodes if n.get("component") == rule["component"]]
        if not found:
            required = screen in rule.get("required_when_screen_in", [])
            return (not required), f"{rule['component']} 없음" + (" (이 화면에서 필수)" if required else " (n/a)")
        bad = [(n["name"], n.get("default_value")) for n in found if n.get("default_value") != rule["value"]]
        return not bad, f"기본값 불일치 {bad}" if bad else "ok"
    if c == "text_regex_count":
        pats = [re.compile(p) for p in rule["patterns"]]
        texts = [(n["name"], str(v)) for _, n in nodes for v in (n.get("text"), n.get("default_value")) if v]
        hits = [(name, m.group(0)) for name, t in texts for p in pats for m in p.finditer(t)]
        return compare(len(hits), rule["op"], rule["value"]), f"검출 {len(hits)}건 {hits}"

    return False, f"알 수 없는 check: {c}"


def compare(a, op, b):
    return {">=": a >= b, "<=": a <= b, "==": a == b, ">": a > b, "<": a < b}[op]


def judge(gate, run_dir, rules=None):
    rules = rules or load_rules()
    screen = os.path.basename(os.path.normpath(run_dir))
    results = []
    for rule in rules["gates"][gate]:
        try:
            ok, detail = check(rule, run_dir, screen, rules)
        except Exception as e:  # 형식 오류도 실패로 센다
            ok, detail = False, f"판정 오류: {type(e).__name__}: {e}"
        results.append({"id": rule["id"], "pass": ok, "severity": rule.get("severity", "design" if gate == "S5" else "gate"),
                        "detail": detail, "source": rule.get("source")})
    failed = [r for r in results if not r["pass"]]
    out = {"gate": gate, "screen": screen, "pass": not failed,
           "failed_rules": [r["id"] for r in failed], "results": results}
    if gate == "S5" and failed:
        out["on_fail"] = rules["on_fail"]["S5.story-service" if any(r["severity"] == "story-service" for r in failed) else "S5.design"]
    elif failed:
        out["on_fail"] = rules["on_fail"][gate]
    return out


# ---------- selftest ----------

def apply_op(run_dir, op):
    path = os.path.join(run_dir, op["file"])
    kind = op["op"]
    if kind == "replace":
        text = open(path, encoding="utf-8").read()
        if op["old"] not in text:
            raise ValueError(f"replace 대상 없음: {op['old']!r} in {op['file']}")
        open(path, "w", encoding="utf-8").write(text.replace(op["old"], op["new"], 1))
        return
    data = json.load(open(path, encoding="utf-8"))
    if kind == "slice":
        data = data[: op["n"]]
    elif kind == "del_key":
        del data[op["index"]][op["key"]]
    elif kind == "frame_set":
        data["frames"][0][op["key"]] = op["value"]
    elif kind == "node_set":
        node = next(n for n in data["frames"][0]["nodes"] if n["name"] == op["node"])
        *parents, last = op["key"].split(".")
        for p in parents:
            node = node[p]
        node[last] = op["value"]
    else:
        raise ValueError(f"알 수 없는 op: {kind}")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def selftest():
    rules = load_rules()
    gates = [g for g, v in rules["gates"].items() if isinstance(v, list)]
    all_ids = [r["id"] for g in gates for r in rules["gates"][g]]
    base = os.path.join(FIXTURES, "pass", "my-assets")
    cases = json.load(open(os.path.join(FIXTURES, "fail-cases.json"), encoding="utf-8"))
    report, ok_all = [], True

    def run_all(run_dir):
        return {rid for g in gates for rid in judge(g, run_dir, rules)["failed_rules"]}

    failed = run_all(base)
    ok = not failed
    ok_all &= ok
    report.append({"case": "pass-fixture", "expect": [], "got": sorted(failed), "ok": ok})

    covered = {c["rule"] for c in cases}
    missing = [rid for rid in all_ids if rid not in covered]
    story = [r["id"] for g in gates for r in rules["gates"][g] if r.get("severity") == "story-service"]
    missing_story = [rid for rid in story if rid not in covered]

    for case in cases:
        tmp = tempfile.mkdtemp()
        try:
            run_dir = os.path.join(tmp, case.get("screen", "my-assets"))
            shutil.copytree(base, run_dir)
            for op in case["ops"]:
                apply_op(run_dir, op)
            got = run_all(run_dir)
            ok = got == {case["rule"]}
        except Exception as e:
            got, ok = {f"오류: {e}"}, False
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok_all &= ok
        report.append({"case": case["rule"], "expect": [case["rule"]], "got": sorted(got), "ok": ok})

    ok_all &= not missing_story
    summary = {"selftest": "pass" if ok_all else "fail", "rules": len(all_ids),
               "cases": len(cases), "cases_failed": [r["case"] for r in report if not r["ok"]],
               "rules_without_fail_case": missing, "story_service_without_fail_case": missing_story,
               "report": report}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if ok_all else 1


def main(argv):
    if argv[1:] == ["--selftest"]:
        return selftest()
    if len(argv) != 3 or argv[1] not in ("G1", "G2", "G3", "S5"):
        print(__doc__, file=sys.stderr)
        return 2
    if not os.path.isdir(argv[2]):
        print(f"실행 폴더 없음: {argv[2]}", file=sys.stderr)
        return 2
    out = judge(argv[1], argv[2])
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
