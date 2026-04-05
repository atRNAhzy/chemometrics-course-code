from __future__ import annotations

import argparse
import json
import re
import subprocess
import threading
import time
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "results" / "autogluon_30min_v2" / "train_stream.log"
SEARCH_SCRIPT = ROOT / "autogluon_search.py"
METRICS_PATH = ROOT / "results" / "autogluon_30min_v2" / "metrics.json"
PUSH_API = "https://www.pushplus.plus/send"


class State:
    def __init__(self) -> None:
        self.best_score = float("-inf")
        self.best_model = "N/A"
        self.latest_ensemble = "N/A"
        self.last_line = ""
        self.lock = threading.Lock()


def push(token: str, title: str, content: str) -> None:
    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(PUSH_API, data=data, headers={"Content-Type": "application/json"})
    with request.urlopen(req, timeout=20) as resp:
        resp.read()


def reader(proc: subprocess.Popen[str], state: State) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    current_model = ""

    with LOG_PATH.open("w", encoding="utf-8") as f:
        for line in proc.stdout:  # type: ignore[arg-type]
            f.write(line)
            f.flush()

            with state.lock:
                state.last_line = line.strip()

            m_fit = re.search(r"Fitting model:\s*([A-Za-z0-9_]+)", line)
            if m_fit:
                current_model = m_fit.group(1)

            m_val = re.search(r"([0-9]+\.[0-9]+)\s*=\s*Validation score\s*\(r2\)", line)
            if m_val and current_model:
                score = float(m_val.group(1))
                with state.lock:
                    if score > state.best_score:
                        state.best_score = score
                        state.best_model = current_model

            m_ens = re.search(r"Ensemble Weights:\s*(\{.*\})", line)
            if m_ens:
                with state.lock:
                    state.latest_ensemble = m_ens.group(1)

            m_best = re.search(r"Best model:\s*([A-Za-z0-9_]+)", line)
            if m_best:
                with state.lock:
                    state.best_model = m_best.group(1)


def monitor_and_push(proc: subprocess.Popen[str], state: State, token: str) -> None:
    push(token, "Wine训练已启动", "开始AutoGluon 30分钟内搜索，后续每2分钟推送当前最佳R²。")
    while proc.poll() is None:
        time.sleep(120)
        with state.lock:
            score = state.best_score
            model = state.best_model
            ensemble = state.latest_ensemble
            last_line = state.last_line[-300:]
        score_text = "N/A" if score == float("-inf") else f"{score:.4f}"
        content = (
            f"### AutoGluon中间进度\n"
            f"- 当前最佳模型: `{model}`\n"
            f"- 当前最佳验证R²: `{score_text}`\n"
            f"- 最近集成结构: `{ensemble}`\n"
            f"- 最新日志: `{last_line}`"
        )
        try:
            push(token, "Wine训练进度(2min)", content)
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    proc = subprocess.Popen(
        ["python", str(SEARCH_SCRIPT)],
        cwd=str(ROOT.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    state = State()
    t_reader = threading.Thread(target=reader, args=(proc, state), daemon=True)
    t_reader.start()

    monitor_and_push(proc, state, args.token)
    code = proc.wait()
    t_reader.join(timeout=5)

    final_msg = f"训练结束，exit code={code}。"
    if METRICS_PATH.exists():
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        final_msg += (
            f"\n\n### Final Metrics\n"
            f"- best_model: `{metrics.get('best_model')}`\n"
            f"- r2: `{metrics.get('r2')}`\n"
            f"- rmse: `{metrics.get('rmse')}`\n"
            f"- mae: `{metrics.get('mae')}`"
        )

    try:
        push(args.token, "Wine训练完成", final_msg)
    except Exception:
        pass

    print(final_msg)


if __name__ == "__main__":
    main()
