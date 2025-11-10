import sqlite3
from typing import Callable, List, Tuple, Dict, Any, Optional
from tools import ToolRegistry
from prompts import build_prompt
from utils import parse_action, extract_section

# at top of agent.py
from dataclasses import dataclass, field
import json
import re

@dataclass
class EvidenceCache:
    tables: list = field(default_factory=list)
    schema: dict = field(default_factory=dict)  # table -> [cols...]
    row_counts: dict = field(default_factory=dict)  # table -> int

def _norm_table_arg(args: Dict[str, Any]) -> Dict[str, Any]:
    # allow describe_table{"table": "sample"} or {"table_name": "sample"}
    if "table" in args:
        args["table_name"] = args["table"]
    return args


# ANSI color codes for readability
class Colors:
    HEADER = "\033[95m"      # purple
    THOUGHT = "\033[96m"     # cyan
    ACTION = "\033[93m"      # yellow
    OBS = "\033[92m"         # green
    ERROR = "\033[91m"       # red
    STEP = "\033[94m"        # blue
    END = "\033[0m"          # reset color

class SQLAgent:
    def __init__(self, llm_complete: Callable[[str], str], db_path: str, step_limit: int = 10):
        try:
            self.conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5.0)
        except sqlite3.OperationalError:
            self.conn = sqlite3.connect(db_path, timeout=5.0)
        self.conn.execute("PRAGMA query_only = ON;")
        self.registry = ToolRegistry(self.conn)
        self.llm_complete = llm_complete
        self.step_limit = step_limit
        self.history_blocks: List[str] = []
        self.logs: List[str] = []
        self.cache = EvidenceCache()

    def _call_tool(self, name: str, args: Dict[str, Any]) -> str:
        # normalize common arg aliases
        if name == "describe_table":
            args = _norm_table_arg(args)

        tool = self.registry.get_tool(name)
        try:
            out = tool.call(**args)
            # update cache opportunistically
            self._ingest_observation(name, out, args)
            # normalize to short text
            if isinstance(out, (list, tuple, set)):
                return str(list(out))[:2000]
            if isinstance(out, dict):
                body = json.dumps(out) if not isinstance(out, str) else out
                if len(body) > 2000: body = body[:2000] + " ...[truncated]"
                return body
            return str(out)[:2000]
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}"

    def _ingest_observation(self, tool_name: str, out: Any, args: Dict[str, Any]):
        # Recognize structures from your tools
        try:
            if tool_name == "list_tables":
                if isinstance(out, (list, tuple)): self.cache.tables = list(out)
                elif isinstance(out, dict) and "tables" in out: self.cache.tables = out["tables"]
            elif tool_name == "describe_table":
                tbl = args.get("table_name") or args.get("table")
                if isinstance(out, dict):
                    cols = out.get("columns")
                    if isinstance(cols, list):
                        # support either list[str] or list[{name:..., type:...}]
                        if cols and isinstance(cols[0], dict) and "name" in cols[0]:
                            self.cache.schema[tbl] = [c["name"] for c in cols]
                        else:
                            self.cache.schema[tbl] = cols
                    rc = out.get("row_count")
                    if isinstance(rc, int): self.cache.row_counts[tbl] = rc
            elif tool_name in ("run_query", "query_database"):
                # Try to parse SELECT COUNT(*) AS x FROM table
                if isinstance(out, dict) and "rows" in out and out["rows"]:
                    # leave generic; validator will read rows as needed
                    pass
        except Exception:
            pass  # never block on cache issues

    def _has_fresh_evidence_this_turn(self, step_start_len: int) -> bool:
        # Did we add at least one THOUGHT/ACTION/OBSERVATION block this step?
        return len(self.history_blocks) > step_start_len

    def _validate_final_against_evidence(self, final: str) -> Optional[str]:
        """
        Light check — returns warning string only for clear contradictions.
        """
        text = final.lower()

        # Check table mismatch
        if self.cache.tables and "table" in text:
            known = set(map(str.lower, self.cache.tables))
            mentioned = {m.strip("'").lower() for m in known if m in text}
            if not mentioned.issubset(known):
                return f"Warning: Answer tables don’t match known tables {sorted(known)}."

        # Check row count mismatch (only if a number is explicitly claimed)
        if "sample" in self.cache.row_counts:
            rc = self.cache.row_counts["sample"]
            m = re.search(r"(\d{2,6})\s+rows", text)
            if m:
                claimed = int(m.group(1))
                if abs(claimed - rc) > 5:  # small tolerance
                    return f"Warning: Claimed {claimed} rows, actual {rc}."

        return None


    def run(self, user_query: str) -> str:
        """
        ReAct loop with mild safety — allows FINAL ANSWER if evidence exists.
        Only warns if the answer clearly contradicts tool results.
        """
        
        for step in range(self.step_limit):
            step_start_len = len(self.history_blocks)
            prompt = build_prompt(
                tool_docs=self.registry.get_tool_descriptions(),
                history_blocks=self.history_blocks,
                user_query=user_query,
            )
            llm_out = self.llm_complete(prompt)

            thought = extract_section(llm_out, "THOUGHT")
            self.logs.append(f"[STEP {step}] THOUGHT: {thought or '(none)'}")

            # ✅ Check for FINAL ANSWER
            final = extract_section(llm_out, "FINAL ANSWER")
            if final:
                # ✅ Require at least one evidence step in total
                if not self.history_blocks:
                    obs = (
                        "You are answering without running any tool yet. "
                        "Please gather evidence using one ACTION before concluding."
                    )
                    self.history_blocks.append(
                        f"THOUGHT: {thought or '(none)'}\nACTION: N/A\nOBSERVATION: {obs}"
                    )
                    continue

                # 🟡 Warn if no new evidence in this turn
                if not self._has_fresh_evidence_this_turn(step_start_len):
                    print(f"\033[93m[Warning]\033[0m No new evidence gathered this turn before FINAL ANSWER.")
                
                # ✅ Accept the final answer (non-blocking)
                mismatch = self._validate_final_against_evidence(final)
                if mismatch:
                    print(f"\033[93m[Warning]\033[0m {mismatch}")
                return final


            # ✅ Parse ACTION
            try:
                tool_name, args = parse_action(llm_out)
            except Exception as e:
                obs = f"ParserError: {e}. Ensure valid JSON with double quotes."
                self.history_blocks.append(
                    f"THOUGHT: {thought or '(parsing failed)'}\nACTION: N/A\nOBSERVATION: {obs}"
                )
                continue

            # ✅ Dispatch
            observation = self._call_tool(tool_name, args)
            print(f"\033[96m[Step {step+1} Observation]\033[0m {observation}")

            # ✅ Append trace
            self.history_blocks.append(
                f"THOUGHT: {thought or '(none)'}\n"
                f"ACTION: {tool_name}{args}\n"
                f"OBSERVATION: {observation}"
            )

        return ("Max step limit reached. Here's what I tried:\n" +
                "\n\n".join(self.history_blocks[-3:]) +
                "\n\nConsider refining the question or being more specific.")



    @staticmethod
    def _block(thought: Optional[str], action_str: str, observation: str) -> str:
        t = f"THOUGHT: {thought.strip()}" if thought else "THOUGHT: (none)"
        return f"{t}\nACTION: {action_str}\nOBSERVATION: {observation}"
