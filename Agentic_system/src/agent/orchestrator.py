import json
import re
from datetime import datetime
from uuid import uuid4

# Project imports
from src.agent.state import AgentState
from src.llm.prompts import (
    BASELINE_SYSTEM,
    AGENT_REVISION_SYSTEM,
    DICT_SUMMARY_SYSTEM,
    FEW_SHOT_SYSTEM,
    GLOSSARY_SYSTEM_ADDENDUM,
)
from src.tools.dict_lookup import DictionaryLookupTool
from src.tools.morph_lookup import MorphAnalysisTool
from src.tools.glossary_lookup import GlossaryLookupTool
from src.db.duckdb_conn import get_db_connection


class SanskritAgent:
    def __init__(self, llm):
        self.llm = llm
        self.dict_tool = DictionaryLookupTool()
        self.morph_tool = MorphAnalysisTool()
        self.glossary_tool = GlossaryLookupTool()

    def _clean_response(self, text: str) -> str:
        """
        Clean the LLM output by removing common boilerplate prefixes.
        """
        if not text:
            return ""

        patterns = [
            r"^(Here is|The translation|The meaning|Output|The English translation).*?:",
            r"^Translation:",
            r"^Revised Translation:",
            r"^Answer:",
            r"^Summary:",
        ]

        cleaned = text
        for p in patterns:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE | re.MULTILINE)

        return cleaned.strip().strip('"').strip("'").strip()

    def _summarize_dictionary_entry(self, word: str, raw_entry: str) -> str:
        """
        Use the LLM to compress a long dictionary entry into a structured summary.
        """
        if len(raw_entry) < 50 or "No entry found" in raw_entry:
            return raw_entry

        messages = [
            {"role": "system", "content": DICT_SUMMARY_SYSTEM},
            {"role": "user", "content": f"Word: {word}\nRaw Entry: {raw_entry}"},
        ]

        # Limit tokens to encourage concise summaries
        summary = self.llm.generate(messages, max_new_tokens=100)
        return self._clean_response(summary)

    def run(
        self,
        src_text: str,
        use_grammar: bool = True,
        use_dict: bool = True,
        few_shot_text: str | None = None,
        use_glossary: bool = False,
    ) -> AgentState:
        """
        Run the translation pipeline.

        Args:
            src_text: Sanskrit input text.
            use_grammar: Enable morphology/grammar lookup.
            use_dict: Enable dictionary lookup.
            few_shot_text: Optional few-shot examples to guide style.
            use_glossary: Enable glossary constraints (terminology enforcement).

        Returns:
            AgentState with draft/final translations and logs.
        """
        run_id = str(uuid4())
        state = AgentState(src_text=src_text)

        # ----------------------------------------------------
        # Step 0: Glossary Lookup (Global Constraint)
        # ----------------------------------------------------
        glossary_text = ""
        glossary_matches: dict[str, str] = {}

        if use_glossary:
            glossary_matches = self.glossary_tool.run(src_text)
            if glossary_matches:
                entries = [f"- {term}: {defn}" for term, defn in glossary_matches.items()]
                glossary_text = GLOSSARY_SYSTEM_ADDENDUM.format(
                    glossary_content="\n".join(entries)
                )
                state.logs.append(f"Step 0: Glossary applied for {len(glossary_matches)} terms.")
            else:
                state.logs.append("Step 0: Glossary enabled but no terms found.")

        # ----------------------------------------------------
        # Step 1: Draft Translation
        # ----------------------------------------------------
        state.logs.append("Step 1: Generating draft translation...")

        # Build system prompt
        base_system = BASELINE_SYSTEM
        if few_shot_text:
            base_system = (
                FEW_SHOT_SYSTEM
                + "\n\n=== REFERENCE EXAMPLES (STYLE GUIDE) ===\n"
                + few_shot_text
            )
            state.logs.append("Step 1: Using few-shot context.")

        # Inject glossary constraints at the end to increase weight
        full_system_prompt = base_system + glossary_text

        draft_messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": f"Translate this Sanskrit text to English:\n{src_text}"},
        ]

        raw_draft = self.llm.generate(draft_messages)
        state.draft_translation = self._clean_response(raw_draft)

        # ----------------------------------------------------
        # Step 2: Grammar / Morphology
        # ----------------------------------------------------
        raw_words = [w.strip("|,.;-") for w in src_text.split() if len(w) > 1]
        morph_evidence: dict[str, str] = {}
        lemmas_to_lookup: set[str] = set()

        if use_grammar:
            state.logs.append("Step 2: Analyzing morphology (Ambuda)...")
            for w in raw_words:
                res = self.morph_tool.run(w)
                if res.get("found"):
                    best_analysis = res["analyses"][0]
                    lemma = best_analysis["lemma"]
                    morph_evidence[w] = f"Lemma: {lemma} | Tags: {best_analysis['tags']}"
                    lemmas_to_lookup.add(lemma)
                else:
                    lemmas_to_lookup.add(w)
        else:
            state.logs.append("Step 2: Morphology analysis skipped.")
            for w in raw_words:
                lemmas_to_lookup.add(w)

        # ----------------------------------------------------
        # Step 3: Dictionary Lookup
        # ----------------------------------------------------
        raw_dict_evidence: dict[str, str] = {}

        if use_dict:
            state.logs.append("Step 3: Looking up dictionary entries...")
            if lemmas_to_lookup:
                raw_dict_evidence = self.dict_tool.run(list(lemmas_to_lookup))
                # Filter invalid results
                raw_dict_evidence = {
                    k: v for k, v in raw_dict_evidence.items() if "No entry found" not in v
                }
            else:
                state.logs.append("Step 3: No terms to look up.")
        else:
            state.logs.append("Step 3: Dictionary lookup skipped.")

        # ----------------------------------------------------
        # Step 3.5: Summarization
        # ----------------------------------------------------
        state.dict_evidence = {}

        if use_dict and raw_dict_evidence:
            state.logs.append("Step 3.5: Summarizing dictionary evidence...")
            for w, raw_content in raw_dict_evidence.items():
                state.dict_evidence[w] = self._summarize_dictionary_entry(w, raw_content)

        # ----------------------------------------------------
        # Step 4: Revision
        # ----------------------------------------------------
        state.logs.append("Step 4: Revising translation...")

        evidence_lines: list[str] = []

        if use_grammar and morph_evidence:
            evidence_lines.append("--- Morphological Analysis ---")
            for w, info in morph_evidence.items():
                evidence_lines.append(f"Token '{w}': {info}")

        if use_dict and state.dict_evidence:
            evidence_lines.append("\n--- Dictionary Definitions ---")
            for w, summary in state.dict_evidence.items():
                evidence_lines.append(f"Term '{w}':\n{summary}")

        full_evidence_text = "\n".join(evidence_lines)

        # If no evidence collected, return draft as final
        if not full_evidence_text.strip():
            state.logs.append("No evidence collected. Skipping revision.")
            state.final_translation = state.draft_translation
        else:
            revision_prompt = f"""
Original Text: {src_text}
Draft Translation: {state.draft_translation}

STRUCTURED EVIDENCE:
{full_evidence_text}

Task:
1) Use the STRUCTURED EVIDENCE to correct the draft.
2) Output ONLY the REVISED English translation.
""".strip()

            # Re-emphasize glossary during revision to prevent overwriting required terms
            rev_msgs = [
                {"role": "system", "content": AGENT_REVISION_SYSTEM + glossary_text},
                {"role": "user", "content": revision_prompt},
            ]

            raw_final = self.llm.generate(rev_msgs)
            state.final_translation = self._clean_response(raw_final)

        # ----------------------------------------------------
        # Save Result
        # ----------------------------------------------------
        if use_dict and use_grammar:
            mode_str = "agent_full"
        elif use_dict:
            mode_str = "agent_dict_only"
        elif use_grammar:
            mode_str = "agent_grammar_only"
        else:
            mode_str = "agent_baseline_fallback"

        if few_shot_text:
            mode_str += "_fewshot"
        if use_glossary:
            mode_str += "_glossary"

        self._save_result(run_id, state, morph_evidence, mode_str)
        return state

    def _save_result(self, run_id: str, state: AgentState, morph_evidence: dict, mode_str: str) -> None:
        """
        Persist the run result into DuckDB.
        """
        try:
            con = get_db_connection()

            combined_evidence = {
                "morphology": morph_evidence,
                "dictionary_summary": state.dict_evidence,
            }

            con.execute(
                """
                INSERT INTO translations (
                    run_id, timestamp, mode, src_text, final_text,
                    tool_calls_json, step_summaries_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    datetime.now(),
                    mode_str,
                    state.src_text,
                    state.final_translation,
                    json.dumps(combined_evidence),
                    json.dumps(state.logs),
                ),
            )

            con.close()

        except Exception as e:
            print(f"Error saving to DB: {e}")
