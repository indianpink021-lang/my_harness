#!/usr/bin/env python3
"""PreToolUse hook: 에이전트별 편집 폴더 강제 (harness/r6-roles.md).

- 모든 주체: docs/, harness/rules.json, harness/judge.py 수정 금지
- runs/<screen>/s1~s3/: 해당 단계 에이전트만 / s4/: 사람만 (Claude 전원 금지)
- runs/<screen>/state.json, s5/: 메인 세션(오케스트레이터)만
- 단계 에이전트는 자기 폴더 밖 쓰기 금지, gate-judge 는 쓰기 전면 금지
- gate-judge 의 Bash 는 `python3 harness/judge.py ...` 만 허용
차단 시 exit 2 + stderr 메시지.
"""
import json
import os
import re
import sys

ROOT = os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR")
                        or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
PROTECTED = ("docs/", "harness/rules.json", "harness/judge.py")
STAGE_AGENT = {"s1": "ref-collector", "s2": "ref-analyst", "s3": "spec-writer"}
AGENT_STAGE = {v: k for k, v in STAGE_AGENT.items()}
RUN_PATH = re.compile(r"^runs/([^/]+)/(?:(s[1-5])/[^/]+|state\.json)$")


def block(msg):
    print(f"[guard-paths] 차단: {msg}", file=sys.stderr)
    sys.exit(2)


def screens():
    try:
        with open(os.path.join(ROOT, "harness", "rules.json"), encoding="utf-8") as f:
            return set(json.load(f)["screens"].values())
    except Exception:
        return set()


def rel(path, cwd):
    p = os.path.realpath(path if os.path.isabs(path) else os.path.join(cwd or ROOT, path))
    if p != ROOT and not p.startswith(ROOT + os.sep):
        return None  # 프로젝트 밖
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def check_write(r, agent):
    if r is None:
        if agent:
            block("에이전트는 프로젝트 밖에 쓸 수 없습니다.")
        return
    if any(r == p.rstrip("/") or r.startswith(p) for p in PROTECTED):
        block(f"{r} 는 읽기 전용입니다 (docs/, rules.json, judge.py).")
    if agent == "gate-judge":
        block("gate-judge 는 읽기 전용 판정자라 파일을 쓸 수 없습니다.")

    m = RUN_PATH.match(r)
    if r.startswith("runs/"):
        if not m:
            block(f"{r}: runs/ 아래 허용 경로는 runs/<screen>/s1~s5/<파일> 또는 runs/<screen>/state.json 뿐입니다.")
        if m.group(1) not in screens():
            block(f"{m.group(1)} 는 rules.json.screens 에 없는 화면입니다.")
        stage = m.group(2)
        if stage == "s4":
            block("s4/ 는 사람 전용입니다. 04-approval.md 를 대신 쓰지 않습니다.")
        if stage in STAGE_AGENT:
            if agent != STAGE_AGENT[stage]:
                block(f"{stage}/ 는 {STAGE_AGENT[stage]} 전용입니다 (현재: {agent or '메인 세션'}).")
            return
        # state.json 또는 s5/
        if agent:
            block(f"{r} 는 오케스트레이터(메인 세션) 전용입니다.")
        return

    if agent in AGENT_STAGE:
        block(f"{agent} 는 runs/<screen>/{AGENT_STAGE[agent]}/ 밖에 쓸 수 없습니다.")


def check_bash(cmd, agent):
    if agent == "gate-judge":
        if not re.fullmatch(r"\s*python3 harness/judge\.py (?:G1|G2|G3|S5) runs/[a-z-]+/?\s*", cmd):
            block("gate-judge 는 `python3 harness/judge.py <G1|G2|G3|S5> runs/<screen>` 만 실행할 수 있습니다.")
        return
    # 메인 세션: 보호 파일을 셸로 바꾸는 흔한 패턴만 막는다 (최선 노력).
    if re.match(r"\s*python3 harness/judge\.py\b", cmd):
        return
    writes = re.search(r">|\btee\b|\bsed\s+-i|\brm\b|\bmv\b|\bcp\b|\btruncate\b|\bchmod\b", cmd)
    touches = re.search(r"docs/|rules\.json|judge\.py|/s4/|\bs4/", cmd)
    if writes and touches:
        block("셸로 보호 경로(docs/, rules.json, judge.py, s4/)를 변경할 수 없습니다.")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    agent = data.get("agent_type") or None
    if tool == "Bash":
        check_bash(ti.get("command", ""), agent)
    elif tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path")
        if path:
            check_write(rel(path, data.get("cwd")), agent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
