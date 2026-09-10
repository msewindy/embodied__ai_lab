"""CTRL-SIM 执行器：自动 launch / 附着 bridge，跑 profile，落盘 manifest。"""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

from lab_platform.config import LabConfig
from lab_platform.models import RunExecutionResult

CTRL_SIM_DOMAIN = 43
DEFAULT_BACKEND = "isaac_sim"
DEFAULT_SCENE = "tabletop_pickplace_v0"
LAUNCH_WAIT_S = 30.0


def resolve_ros2_bin() -> str | None:
    """Locate ros2 CLI even when venv activation shadows PATH."""
    found = shutil.which("ros2")
    if found:
        return found
    distro = os.environ.get("ROS_DISTRO", "jazzy")
    candidates = [
        Path(f"/opt/ros/{distro}/bin/ros2"),
        Path("/opt/ros/jazzy/bin/ros2"),
    ]
    for p in candidates:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
    return None


def ros2_missing_hint() -> str:
    return (
        "ros2 CLI not found. In this shell run:\n"
        "  source /opt/ros/jazzy/setup.bash\n"
        "  export ROS_DOMAIN_ID=43 RMW_IMPLEMENTATION=rmw_cyclonedds_cpp\n"
        "  source ~/project/embodied__ai_lab/ros2/install/setup.bash\n"
        "  cd ~/project/embodied__ai_lab/lab_platform && source .venv/bin/activate"
    )


def _script_path(name: str) -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "scripts" / name,
        here.parents[3] / "lab_platform" / "scripts" / name,
    ]
    for p in candidates:
        if p.is_file():
            return p
    return candidates[0]


def _hello_script() -> Path:
    return _script_path("m2_franka_hello.py")


def _m5_script() -> Path:
    return _script_path("m5_mid_template.py")


def _policy_rollout_script() -> Path:
    return _script_path("m5_policy_rollout.py")


def _resolve_policy_checkpoint(
    override: str | None,
    profile_yaml: Path | None,
    data_root: Path,
) -> Path | None:
    """CLI override > profile checkpoint（绝对路径或相对 data_root）。"""
    import yaml

    candidates: list[Path] = []
    if override:
        candidates.append(Path(override).expanduser())
    if profile_yaml is not None and profile_yaml.is_file():
        raw = yaml.safe_load(profile_yaml.read_text(encoding="utf-8")) or {}
        rel = raw.get("checkpoint")
        if rel:
            candidates.append(Path(str(rel)).expanduser())
    for c in candidates:
        if c.is_file():
            return c.resolve()
        under = (Path(data_root) / c).resolve()
        if under.is_file():
            return under
    return None


def _read_isaac_version() -> str:
    candidates = [
        Path(os.environ.get("ISAACSIM_PATH", "")) / "VERSION",
        Path.home() / "isaacsim" / "VERSION",
        Path("/home/ljqy/isaacsim/VERSION"),
    ]
    for p in candidates:
        if p.is_file():
            return p.read_text(encoding="utf-8").strip()
    return "unknown"


def _ros_env(domain: int) -> dict[str, str]:
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = str(domain)
    env.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")
    return env


def _topic_list(domain: int) -> list[str]:
    ros2 = resolve_ros2_bin()
    if not ros2:
        return [f"__error__:{ros2_missing_hint()}"]
    try:
        proc = subprocess.run(
            [ros2, "topic", "list"],
            capture_output=True,
            text=True,
            env=_ros_env(domain),
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return [f"__error__:{e}"]
    if proc.returncode != 0:
        return [f"__error__:{proc.stderr.strip() or proc.stdout.strip()}"]
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def _echo_run_context(domain: int, timeout_s: float = 3.0) -> dict | None:
    ros2 = resolve_ros2_bin()
    if not ros2:
        return None
    try:
        proc = subprocess.run(
            [
                ros2,
                "topic",
                "echo",
                "/system/run_context",
                "--once",
                "--qos-durability",
                "transient_local",
                "--qos-reliability",
                "reliable",
            ],
            capture_output=True,
            text=True,
            env=_ros_env(domain),
            timeout=timeout_s,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    # 粗解析 yaml-ish echo 输出
    out: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip("'\"")
        if key in ("run_id", "run_type", "scene_id", "policy_id", "operator_id"):
            out[key] = val
    return out or {"raw": proc.stdout.strip()[:500]}


class CtrlSimLauncher:
    """非 Stub：必要时自动拉起 franka_ctrl_sim.launch，执行 hello，写 manifest。"""

    def __init__(self, config: LabConfig) -> None:
        self._config = config
        self._launch_proc: subprocess.Popen | None = None
        self.auto_launch: bool = True
        self.keep_launch: bool = False
        self.record: bool = False
        self.record_fps: float = 10.0
        self.policy_checkpoint: str | None = None
        self.policy_id: str | None = None

    def run(
        self,
        *,
        run_id: str,
        run_dir: Path,
        device_id: str,
        scene_id: str,
        profile: str,
        backend: str = DEFAULT_BACKEND,
        domain: int = CTRL_SIM_DOMAIN,
        auto_launch: bool | None = None,
        keep_launch: bool | None = None,
        record: bool | None = None,
        record_fps: float | None = None,
        dx: float = 0.05,
        policy_checkpoint: str | None = None,
    ) -> RunExecutionResult:
        if auto_launch is None:
            auto_launch = self.auto_launch
        if keep_launch is None:
            keep_launch = self.keep_launch
        if record is None:
            record = self.record
        if record_fps is None:
            record_fps = self.record_fps

        logs = run_dir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        os.environ["ROS_DOMAIN_ID"] = str(domain)
        os.environ.setdefault("RMW_IMPLEMENTATION", "rmw_cyclonedds_cpp")

        from lab_platform.ctrl_sim.task_pack import (
            TaskPackError,
            resolve_scene_for_ctrl_sim,
        )

        sid = scene_id or DEFAULT_SCENE
        try:
            pack, pack_warn = resolve_scene_for_ctrl_sim(
                sid, data_root=self._config.data_root
            )
        except TaskPackError as e:
            return RunExecutionResult(
                False,
                f"Task Pack error: {e}",
                extra={"scene_id": sid, "ros_domain_id": domain},
            )
        if pack is not None:
            (logs / "scene_pack.json").write_text(
                json.dumps(pack.summary(), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            shutil.copy2(pack.scene_yaml, logs / "scene.yaml")
        elif pack_warn:
            (logs / "scene_pack_warn.txt").write_text(pack_warn + "\n", encoding="utf-8")

        ns = device_id.replace("-", "_")
        lab_topics = [
            f"/skill/{ns}/intent",
            f"/perception/{ns}/low_state",
        ]
        isaac_topics = ["/joint_states"]
        need = ["/joint_states", "/joint_command", *lab_topics]

        topics = _topic_list(domain)
        (logs / "topic_list_before.txt").write_text("\n".join(topics) + "\n", encoding="utf-8")

        if any(t.startswith("__error__:") for t in topics):
            return RunExecutionResult(
                False,
                f"ros2 topic list failed: {topics[0]}",
                extra={"ros_domain_id": domain},
            )

        launched = False
        attach = all(t in topics for t in lab_topics)
        mode = "attach"

        if not attach:
            if not auto_launch:
                missing = [t for t in lab_topics if t not in topics]
                return RunExecutionResult(
                    False,
                    "CTRL-SIM graph not up; missing topics: " + ", ".join(missing),
                    extra={
                        "ros_domain_id": domain,
                        "missing_topics": missing,
                        "hint": (
                            "Start Isaac (official FR3 USD + JointStates Play), then: "
                            "ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py "
                            f"device_id:={device_id} backend:={backend}"
                        ),
                    },
                )
            if not all(t in topics for t in isaac_topics):
                return RunExecutionResult(
                    False,
                    "Isaac JointStates not visible on DOMAIN "
                    f"{domain} (need /joint_states). Start Isaac Play first.",
                    extra={
                        "ros_domain_id": domain,
                        "missing_topics": [t for t in isaac_topics if t not in topics],
                    },
                )
            ok_launch, detail = self._start_launch(
                logs=logs,
                device_id=device_id,
                backend=backend,
                domain=domain,
                wait_topics=lab_topics,
            )
            if not ok_launch:
                self._stop_launch(logs)
                return RunExecutionResult(
                    False,
                    f"auto launch failed: {detail}",
                    extra={"ros_domain_id": domain, "auto_launch": True},
                )
            launched = True
            mode = "launched"
            topics = _topic_list(domain)
            (logs / "topic_list_after_launch.txt").write_text(
                "\n".join(topics) + "\n", encoding="utf-8"
            )

        missing = [t for t in need if t not in topics]
        # joint_command 有时仅在有 publisher 后出现；lab topics + joint_states 足够
        hard_missing = [t for t in (isaac_topics + lab_topics) if t not in topics]
        if hard_missing:
            if launched:
                self._stop_launch(logs)
            return RunExecutionResult(
                False,
                "CTRL-SIM topics still missing: " + ", ".join(hard_missing),
                extra={"ros_domain_id": domain, "mode": mode},
            )

        ctx_snap = _echo_run_context(domain)
        if ctx_snap is not None:
            (logs / "run_context_echo.json").write_text(
                json.dumps(ctx_snap, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        mid_profiles = ("m5_template", "m5_approach_target", "m5_pickplace")
        policy_profiles = ("m5_policy_rollout",)
        if profile not in ("m2_hello",) + mid_profiles + policy_profiles:
            if launched and not keep_launch:
                self._stop_launch(logs)
            return RunExecutionResult(False, f"unsupported profile: {profile}")

        ckpt_arg = policy_checkpoint or self.policy_checkpoint

        if profile == "m2_hello":
            script = _hello_script()
            profile_log = logs / "m2_hello.log"
            cmd = [
                sys.executable,
                str(script),
                "--dx",
                str(dx),
                "--domain",
                str(domain),
                "--device-id",
                device_id,
            ]
            pass_token = "PASS field check"
            timeout_s = 120
        elif profile in policy_profiles:
            script = _policy_rollout_script()
            profile_log = logs / "m5_policy_rollout.log"
            steps_log = logs / "policy_steps.json"
            cmd = [
                sys.executable,
                str(script),
                "--domain",
                str(domain),
                "--device-id",
                device_id,
                "--run-id",
                run_id,
                "--steps-log",
                str(steps_log),
            ]
            tmpl = pack.profile_path(profile) if pack is not None else None
            if tmpl is not None:
                cmd.extend(["--template", str(tmpl)])
            # resolve checkpoint: CLI override → profile relative to data_root
            resolved_ckpt = _resolve_policy_checkpoint(
                ckpt_arg, tmpl, self._config.data_root
            )
            if resolved_ckpt is not None:
                cmd.extend(["--checkpoint", str(resolved_ckpt)])
            pass_token = '"success": true'
            timeout_s = 120
        else:
            script = _m5_script()
            profile_log = logs / "m5_mid_template.log"
            steps_log = logs / "mid_steps.json"
            eval_log = logs / "eval.json"
            cmd = [
                sys.executable,
                str(script),
                "--domain",
                str(domain),
                "--device-id",
                device_id,
                "--run-id",
                run_id,
                "--steps-log",
                str(steps_log),
            ]
            if profile == "m5_pickplace":
                cmd.extend(["--eval-log", str(eval_log)])
            tmpl = pack.profile_path(profile) if pack is not None else None
            if tmpl is not None:
                cmd.extend(["--template", str(tmpl)])
            if pack is not None:
                cmd.extend(["--scene-yaml", str(pack.scene_yaml)])
            pass_token = '"success": true'
            timeout_s = {
                "m5_approach_target": 300,
                "m5_pickplace": 420,
            }.get(profile, 180)

        if not script.is_file():
            if launched and not keep_launch:
                self._stop_launch(logs)
            return RunExecutionResult(False, f"profile script missing: {script}")

        jsonl_path = logs / "low.jsonl"
        record_stats: dict | None = None
        recorder = None
        if record:
            from lab_platform.ctrl_sim.recorder import TrajectoryRecorder

            recorder = TrajectoryRecorder(
                out_path=jsonl_path,
                device_id=device_id,
                domain=domain,
                fps=float(record_fps),
                run_id=run_id,
            )
            recorder.start()
            time.sleep(0.5)
            print(
                f"[CtrlSim] recording → {jsonl_path} fps={record_fps}",
                flush=True,
            )

        try:
            with profile_log.open("w", encoding="utf-8") as fh:
                fh.write(f"$ {' '.join(cmd)}\n")
                fh.flush()
                proc = subprocess.run(
                    cmd,
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=_ros_env(domain),
                    cwd=str(script.parent.parent),
                    timeout=timeout_s,
                    check=False,
                )
        finally:
            if recorder is not None:
                record_stats = recorder.stop()
                (logs / "record_stats.json").write_text(
                    json.dumps(record_stats, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )

        isaac_ver = _read_isaac_version()
        bringup_cmd = (
            "ros2 launch embodied_lab_bringup franka_ctrl_sim.launch.py "
            f"device_id:={device_id} backend:={backend}"
        )
        manifest: dict = {
            "run_id": run_id,
            "run_type": "ctrl_sim",
            "device_id": device_id,
            "device_ids": [device_id],
            "scene_id": sid,
            "backend": backend,
            "ros_domain_id": domain,
            "profile": profile,
            "isaac_sim_version": isaac_ver,
            "mode": mode,
            "auto_launch": auto_launch,
            "launched_by_lab": launched,
            "keep_launch": keep_launch,
            "profile_exit_code": proc.returncode,
            "topics_ok": [t for t in need if t in _topic_list(domain)],
            "run_context_echo": ctx_snap,
            "bringup_launch": bringup_cmd,
        }
        if pack is not None:
            manifest["task_pack"] = pack.summary()
            manifest["task_pack"]["scene_yaml_snapshot"] = "logs/scene.yaml"
        elif pack_warn:
            manifest["task_pack_warn"] = pack_warn
        if profile in mid_profiles:
            steps_path = logs / "mid_steps.json"
            mid_summary = None
            if steps_path.is_file():
                try:
                    mid_summary = json.loads(steps_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    mid_summary = None
            tmpl_rel = (
                str(pack.profile_path(profile).relative_to(pack.root))
                if pack is not None and pack.profile_path(profile) is not None
                else "templates/m5_approach_retreat.yaml"
            )
            manifest["mid"] = {
                "template": tmpl_rel,
                "steps_log": "logs/mid_steps.json",
                "skill_mode": "task_space",
                "scene_yaml": (mid_summary or {}).get("scene_yaml"),
                "oracle_gt": (mid_summary or {}).get("oracle_gt"),
                "num_steps_done": (mid_summary or {}).get("num_steps_done"),
                "steps": (mid_summary or {}).get("steps"),
                "success": (mid_summary or {}).get("success"),
            }
            if (logs / "eval.json").is_file():
                try:
                    eval_doc = json.loads((logs / "eval.json").read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    eval_doc = None
                manifest["eval"] = {
                    "path": "logs/eval.json",
                    "success": (eval_doc or {}).get("success"),
                    "predicates": (eval_doc or {}).get("predicates"),
                }
                if profile == "m5_pickplace" and eval_doc is not None:
                    # 抓放以 eval 为 run 成功依据之一（mid JSON 已对齐）
                    pass
        if profile in policy_profiles:
            steps_path = logs / "policy_steps.json"
            pol_summary = None
            if steps_path.is_file():
                try:
                    pol_summary = json.loads(steps_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    pol_summary = None
            manifest["policy"] = {
                "backend": (pol_summary or {}).get("policy_backend"),
                "checkpoint": (pol_summary or {}).get("checkpoint"),
                "policy_id": self.policy_id,
                "steps_log": "logs/policy_steps.json",
                "n_pub": (pol_summary or {}).get("n_pub"),
                "n_hold": (pol_summary or {}).get("n_hold"),
                "success": (pol_summary or {}).get("success"),
            }
            if self.policy_id:
                manifest["policy_id"] = self.policy_id
        if record and record_stats is not None:
            rel_jsonl = "logs/low.jsonl"
            manifest["tracks"] = {
                "A": {
                    "path": rel_jsonl,
                    "record_fps": record_stats.get("record_fps"),
                    "num_frames": record_stats.get("num_frames"),
                    "topics": record_stats.get("topics"),
                    "duration_s": record_stats.get("duration_s"),
                    "error": record_stats.get("error"),
                }
            }
            manifest["replay"] = {
                "command": (
                    f"lab --data-root <data-root> ctrl-sim replay --run-id {run_id} "
                    f"--device {device_id}"
                ),
                "metrics_path": "logs/replay_metrics.json",
            }
        (run_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        meta_path = run_dir / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}
            meta.update(
                {
                    "backend": backend,
                    "ros_domain_id": domain,
                    "isaac_sim_version": isaac_ver,
                    "scene_id": sid,
                    "profile": profile,
                    "mode": mode,
                    "launched_by_lab": launched,
                    "recorded": bool(record),
                }
            )
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        native = run_dir / "native"
        native.mkdir(exist_ok=True)
        shutil.copy2(profile_log, native / profile_log.name)
        if profile in mid_profiles and (logs / "mid_steps.json").is_file():
            shutil.copy2(logs / "mid_steps.json", native / "mid_steps.json")
        if profile in policy_profiles and (logs / "policy_steps.json").is_file():
            shutil.copy2(logs / "policy_steps.json", native / "policy_steps.json")
        if (logs / "eval.json").is_file():
            shutil.copy2(logs / "eval.json", native / "eval.json")
        if record and jsonl_path.is_file():
            shutil.copy2(jsonl_path, native / "low.jsonl")

        ok = proc.returncode == 0
        log_tail = ""
        try:
            text = profile_log.read_text(encoding="utf-8")
            log_tail = text.strip().splitlines()[-1] if text.strip() else ""
            if pass_token not in text:
                ok = False
        except OSError:
            ok = False
        if record:
            nframes = int((record_stats or {}).get("num_frames") or 0)
            if nframes <= 0:
                ok = False
                log_tail = f"record produced 0 frames; {(record_stats or {}).get('error')}"

        if launched and not keep_launch:
            self._stop_launch(logs)

        msg_ok = f"ctrl_sim {profile} completed"
        msg_fail = f"{profile} failed: {log_tail}"
        return RunExecutionResult(
            ok,
            msg_ok if ok else msg_fail,
            extra={
                "manifest": str(run_dir / "manifest.json"),
                "ros_domain_id": domain,
                "backend": backend,
                "isaac_sim_version": isaac_ver,
                "profile_exit_code": proc.returncode,
                "mode": mode,
                "launched_by_lab": launched,
                "run_context_seen": bool(ctx_snap and ctx_snap.get("run_id")),
                "recorded": bool(record),
                "record_frames": int((record_stats or {}).get("num_frames") or 0),
                "low_jsonl": str(jsonl_path) if record else None,
                "profile": profile,
                "mid_steps": str(logs / "mid_steps.json")
                if profile in mid_profiles
                else None,
                "policy_steps": str(logs / "policy_steps.json")
                if profile in policy_profiles
                else None,
            },
        )

    def _start_launch(
        self,
        *,
        logs: Path,
        device_id: str,
        backend: str,
        domain: int,
        wait_topics: list[str],
    ) -> tuple[bool, str]:
        ros2 = resolve_ros2_bin()
        if not ros2:
            return False, ros2_missing_hint()
        launch_log = logs / "franka_ctrl_sim.launch.log"
        cmd = [
            ros2,
            "launch",
            "embodied_lab_bringup",
            "franka_ctrl_sim.launch.py",
            f"device_id:={device_id}",
            f"backend:={backend}",
        ]
        fh = launch_log.open("w", encoding="utf-8")
        fh.write(f"$ {' '.join(cmd)}\n")
        fh.flush()
        try:
            self._launch_proc = subprocess.Popen(
                cmd,
                stdout=fh,
                stderr=subprocess.STDOUT,
                env=_ros_env(domain),
                start_new_session=True,
            )
        except FileNotFoundError:
            fh.close()
            return False, ros2_missing_hint()
        (logs / "bringup.pid").write_text(str(self._launch_proc.pid) + "\n", encoding="utf-8")
        print(f"[CtrlSim] auto-launch pid={self._launch_proc.pid}: {' '.join(cmd)}")

        deadline = time.time() + LAUNCH_WAIT_S
        while time.time() < deadline:
            if self._launch_proc.poll() is not None:
                fh.flush()
                fh.close()
                return False, f"launch exited early code={self._launch_proc.returncode}"
            topics = _topic_list(domain)
            if all(t in topics for t in wait_topics):
                fh.flush()
                # keep fh open until stop — reopen append for later? close and let proc inherit
                # Actually we passed fh to Popen; must not close until process ends if we want full log.
                # Keep reference on self
                self._launch_log_fh = fh
                return True, "topics ready"
            time.sleep(0.5)

        fh.flush()
        self._launch_log_fh = fh
        return False, f"timeout waiting for {wait_topics} ({LAUNCH_WAIT_S}s)"

    def _stop_launch(self, logs: Path) -> None:
        proc = self._launch_proc
        if proc is None:
            return
        pid = proc.pid
        print(f"[CtrlSim] stopping auto-launched bringup pid={pid}")
        try:
            os.killpg(pid, signal.SIGINT)
        except (ProcessLookupError, PermissionError):
            try:
                proc.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
            proc.wait(timeout=5)
        fh = getattr(self, "_launch_log_fh", None)
        if fh is not None:
            try:
                fh.close()
            except OSError:
                pass
            self._launch_log_fh = None
        self._launch_proc = None
        (logs / "bringup_stopped.txt").write_text(f"stopped pid={pid}\n", encoding="utf-8")
