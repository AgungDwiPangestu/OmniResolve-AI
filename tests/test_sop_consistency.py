"""
tests/test_sop_consistency.py — Validasi Konsistensi SOP

Memastikan aturan bisnis di kode konsisten dengan SOP perusahaan:
1. Threshold HITL: > Rp 1.000.000 WAJIB approval supervisor
2. Bahasa rejection letter: sopan, empatis, tidak kasar
3. Tipe keputusan valid: hanya voucher/replacement/refund/reject
4. Prompt agen mengandung elemen empati

Jalankan: pytest tests/test_sop_consistency.py -v
"""
import pytest

from src.config import get_settings
from src.agents.strategic_negotiator import (
    NEGOTIATOR_SYSTEM_PROMPT,
    should_notify_supervisor,
)
from src.agents.liaison_agent import LIAISON_SYSTEM_PROMPT
from src.agents.supply_chain_orchestrator import RESPONSE_COMPOSER_PROMPT
from src.graph.state import GraphState


class TestSOPThresholdHITL:
    """SOP: Kompensasi > Rp 1.000.000 WAJIB persetujuan supervisor."""

    def test_config_threshold_sesuai_sop(self):
        """Config hitl_threshold_idr harus Rp 1.000.000."""
        settings = get_settings()
        assert settings.hitl_threshold_idr == 1_000_000.0, (
            f"Threshold di config: Rp {settings.hitl_threshold_idr:,.0f}, "
            f"SOP mengharuskan Rp 1.000.000"
        )

    def test_prompt_negotiator_mencantumkan_threshold(self):
        """Prompt negotiator harus menyebutkan batas HITL."""
        assert "1.000.000" in NEGOTIATOR_SYSTEM_PROMPT, (
            "Prompt negotiator tidak menyebutkan threshold Rp 1.000.000"
        )
        assert "requires_human_approval" in NEGOTIATOR_SYSTEM_PROMPT, (
            "Prompt negotiator tidak menyebutkan requires_human_approval"
        )

    def test_routing_hitl_di_bawah_threshold(self):
        """Kompensasi <= threshold → proceed langsung ke orchestrator."""
        mock_state: GraphState = {
            "messages": [],
            "raw_input": "",
            "complaint": None,
            "audit_result": None,
            "audit_retry_count": 0,
            "customer_profile": None,
            "compensation_decision": {
                "decision_type": "voucher",
                "compensation_value_idr": 500_000.0,
                "reasoning": "Test",
                "requires_human_approval": False,
            },
            "orchestrator_action": None,
            "final_response": None,
            "session_id": "test-sop",
            "error": None,
        }
        result = should_notify_supervisor(mock_state)
        assert result == "proceed_to_orchestrator", (
            f"Kompensasi Rp 500K seharusnya proceed, tapi: {result}"
        )

    def test_routing_hitl_di_atas_threshold(self):
        """Kompensasi > threshold → notify supervisor."""
        mock_state: GraphState = {
            "messages": [],
            "raw_input": "",
            "complaint": None,
            "audit_result": None,
            "audit_retry_count": 0,
            "customer_profile": None,
            "compensation_decision": {
                "decision_type": "refund",
                "compensation_value_idr": 2_000_000.0,
                "reasoning": "Test",
                "requires_human_approval": True,
            },
            "orchestrator_action": None,
            "final_response": None,
            "session_id": "test-sop",
            "error": None,
        }
        result = should_notify_supervisor(mock_state)
        assert result == "notify_supervisor", (
            f"Kompensasi Rp 2jt seharusnya notify supervisor, tapi: {result}"
        )


class TestSOPBahasaRejection:
    """SOP: Bahasa penolakan harus sopan dan empatis."""

    def test_prompt_response_composer_empatis(self):
        """Response composer prompt harus mengandung instruksi empati."""
        kata_empati = ["empatik", "profesional", "tidak menggunakan bahasa teknis"]
        for kata in kata_empati:
            assert kata.lower() in RESPONSE_COMPOSER_PROMPT.lower(), (
                f"Prompt response composer tidak mengandung instruksi: '{kata}'"
            )

    def test_prompt_liaison_empatis(self):
        """Liaison prompt harus mengandung instruksi empati."""
        assert "empati" in LIAISON_SYSTEM_PROMPT.lower(), (
            "Prompt liaison tidak mengandung kata 'empati'"
        )
        assert "bahasa indonesia" in LIAISON_SYSTEM_PROMPT.lower(), (
            "Prompt liaison tidak menyebutkan 'Bahasa Indonesia'"
        )

    def test_prompt_negotiator_memiliki_logika_clv(self):
        """Negotiator harus mempertimbangkan CLV dalam keputusan."""
        assert "clv" in NEGOTIATOR_SYSTEM_PROMPT.lower() or \
               "lifetime value" in NEGOTIATOR_SYSTEM_PROMPT.lower(), (
            "Prompt negotiator tidak menyebutkan CLV / Customer Lifetime Value"
        )


class TestSOPTipeKeputusanValid:
    """SOP: Hanya 4 tipe keputusan yang diizinkan."""

    def test_prompt_mendefinisikan_tipe_keputusan(self):
        """Prompt negotiator harus mendefinisikan semua 4 tipe."""
        tipe_valid = ["voucher", "replacement", "refund", "reject"]
        for tipe in tipe_valid:
            assert tipe in NEGOTIATOR_SYSTEM_PROMPT, (
                f"Prompt negotiator tidak mendefinisikan tipe: '{tipe}'"
            )

    def test_prompt_menjelaskan_kondisi_setiap_tipe(self):
        """Prompt harus menjelaskan kapan setiap tipe digunakan."""
        # Voucher untuk barang murah / pelanggan baru
        assert "500.000" in NEGOTIATOR_SYSTEM_PROMPT or "murah" in NEGOTIATOR_SYSTEM_PROMPT.lower()
        # Replacement untuk pelanggan setia
        assert "setia" in NEGOTIATOR_SYSTEM_PROMPT.lower()
        # Refund untuk klaim sangat valid
        assert "refund" in NEGOTIATOR_SYSTEM_PROMPT.lower()
        # Reject dengan penjelasan
        assert "reject" in NEGOTIATOR_SYSTEM_PROMPT.lower()
