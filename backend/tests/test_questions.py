"""
Step 3 — Dynamic Symptom & Follow-Up Question Engine: Comprehensive Test Suite.

Tests:
  1.  GET /api/v1/questions              — list full question bank
  2.  GET /api/v1/questions?category=... — filter by category
  3.  GET /api/v1/questions?priority=emergency — emergency priority filter
  4.  GET /api/v1/questions?species=Feline — species filter
  5.  GET /api/v1/questions?priority=invalid — invalid priority rejected (422)
  6.  GET /next-questions (no symptoms)   — returns questions or empty safely
  7.  GET /next-questions with vomiting   — returns digestive questions
  8.  GET /next-questions with difficulty breathing — emergency questions first
  9.  POST /answers — valid yes/no answer submission
  10. POST /answers — valid single_choice answer submission
  11. POST /answers — valid text answer submission
  12. POST /answers — valid numeric answer submission
  13. POST /answers — duplicate answer rejected (409)
  14. POST /answers — missing question_id rejected (422)
  15. POST /answers — no answer value rejected (422)
  16. POST /answers — invalid question UUID rejected (422)
  17. POST /answers — completed assessment rejected (422)
  18. POST /answers — wrong user rejected (403)
  19. GET  /answers — retrieve all submitted answers
  20. GET  /answers — wrong user rejected (403)
  21. GET  /question-state — progress tracking response shape
  22. GET  /question-state — emergency flags propagated after emergency answer
  23. GET  /question-state — is_ready_for_completion logic
  24. GET  /question-state — wrong user rejected (403)
  25. Conditional question logic — blood answer unlocks digestive questions
  26. Emergency answer triggers emergency flag on assessment state
  27. Species-aware question selection — feline species filter respected
  28. AI payload includes follow_up_answers section
  29. No authentication on GET /questions (public endpoint)
  30. Batch_size parameter respected by next-questions endpoint
"""
import pytest


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vomiting_assessment(client, registered_user, test_pet):
    """Assessment with 'vomiting' symptom attached (Digestive category)."""
    sym_res = client.get("/api/v1/symptoms?category=Digestive")
    symptoms = sym_res.get_json()["data"]
    assert symptoms, "No Digestive symptoms seeded"
    symptom_id = symptoms[0]["id"]

    ass_res = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assessment_id = ass_res.get_json()["data"]["id"]

    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "moderate",
            "duration_value": 2,
            "duration_unit": "days",
        },
    )
    return {"id": assessment_id, "symptom_id": symptom_id}


@pytest.fixture
def breathing_assessment(client, registered_user, test_pet):
    """Assessment with 'difficulty breathing' (emergency) symptom."""
    sym_res = client.get("/api/v1/symptoms?category=Respiratory")
    symptoms = sym_res.get_json()["data"]
    assert symptoms, "No Respiratory symptoms seeded"
    difficulty_breathing = next(
        (s for s in symptoms if "breathing" in s["name"].lower()),
        symptoms[0],
    )
    symptom_id = difficulty_breathing["id"]

    ass_res = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assessment_id = ass_res.get_json()["data"]["id"]

    client.post(
        f"/api/v1/assessments/{assessment_id}/symptoms",
        headers=registered_user["headers"],
        json={
            "symptom_id": symptom_id,
            "severity": "severe",
            "duration_value": 1,
            "duration_unit": "hours",
        },
    )
    return {"id": assessment_id, "symptom_id": symptom_id}


# ---------------------------------------------------------------------------
# 1-5. GET /api/v1/questions — Question Bank Listing
# ---------------------------------------------------------------------------

def test_list_all_questions(client):
    """1. GET /questions returns all active questions with options."""
    res = client.get("/api/v1/questions")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "questions" in data["data"]
    assert "total" in data["data"]
    assert data["data"]["total"] > 0, "Question bank should be seeded"
    q = data["data"]["questions"][0]
    assert "id" in q
    assert "question_text" in q
    assert "question_type" in q
    assert "priority" in q
    assert "options" in q


def test_filter_questions_by_category(client):
    """2. GET /questions?category=Digestive returns only Digestive questions."""
    res = client.get("/api/v1/questions?category=Digestive")
    assert res.status_code == 200
    questions = res.get_json()["data"]["questions"]
    assert len(questions) > 0, "There should be Digestive questions"
    for q in questions:
        assert q["category"] == "Digestive"


def test_filter_questions_by_emergency_priority(client):
    """3. GET /questions?priority=emergency returns only emergency-priority questions."""
    res = client.get("/api/v1/questions?priority=emergency")
    assert res.status_code == 200
    questions = res.get_json()["data"]["questions"]
    assert len(questions) > 0, "There should be emergency-priority questions"
    for q in questions:
        assert q["priority"] == "emergency"
        assert q["is_emergency_related"] is True


def test_filter_questions_by_species(client):
    """4. GET /questions?species=Feline returns questions valid for cats."""
    res = client.get("/api/v1/questions?species=Feline")
    assert res.status_code == 200
    questions = res.get_json()["data"]["questions"]
    for q in questions:
        assert q.get("species") in (None, "Feline")


def test_invalid_priority_filter_rejected(client):
    """5. GET /questions?priority=invalid returns 422."""
    res = client.get("/api/v1/questions?priority=banana")
    assert res.status_code == 422
    assert res.get_json()["success"] is False


def test_questions_endpoint_no_auth_required(client):
    """29. GET /questions is a public endpoint — no JWT needed."""
    res = client.get("/api/v1/questions")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# 6-8. GET /assessments/<id>/next-questions — Dynamic Question Selection
# ---------------------------------------------------------------------------

def test_next_questions_empty_assessment(client, registered_user, test_assessment):
    """6. next-questions on empty assessment returns safe response."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/next-questions",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "questions" in data
    assert "progress" in data
    assert "emergency_flags" in data
    assert "is_ready_for_completion" in data
    assert "safety_message" in data
    assert "veterinary" in data["safety_message"].lower()


def test_next_questions_with_vomiting_symptom(client, registered_user, vomiting_assessment):
    """7. next-questions returns Digestive-category questions when vomiting is selected."""
    res = client.get(
        f"/api/v1/assessments/{vomiting_assessment['id']}/next-questions",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    questions = data["questions"]
    assert len(questions) > 0, "Should return questions for vomiting"
    categories = {q.get("category") for q in questions}
    assert "Digestive" in categories or any(
        "vomit" in q["question_text"].lower() for q in questions
    ), "Vomiting questions should appear"


def test_next_questions_emergency_symptoms_prioritized(
    client, registered_user, breathing_assessment
):
    """8. Emergency questions appear first for difficulty breathing."""
    res = client.get(
        f"/api/v1/assessments/{breathing_assessment['id']}/next-questions",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    questions = data["questions"]
    assert len(questions) > 0
    first_q = questions[0]
    assert first_q["priority"] == "emergency", (
        f"Expected emergency priority first, got: {first_q['priority']}"
    )
    assert first_q["is_emergency_related"] is True


def test_next_questions_batch_size_respected(client, registered_user, vomiting_assessment):
    """30. batch_size query param limits number of returned questions."""
    res = client.get(
        f"/api/v1/assessments/{vomiting_assessment['id']}/next-questions?batch_size=2",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    questions = res.get_json()["data"]["questions"]
    assert len(questions) <= 2


def test_next_questions_requires_auth(client, test_assessment):
    """JWT required on next-questions endpoint."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/next-questions"
    )
    assert res.status_code == 401


def test_next_questions_wrong_user_forbidden(client, second_user, test_assessment):
    """Wrong user gets 403 on next-questions."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/next-questions",
        headers=second_user["headers"],
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# 9-17. POST /assessments/<id>/answers — Answer Submission
# ---------------------------------------------------------------------------

def _get_first_question_for_assessment(client, headers, assessment_id):
    """Helper: get the first question available for an assessment."""
    res = client.get(
        f"/api/v1/assessments/{assessment_id}/next-questions?batch_size=1",
        headers=headers,
    )
    questions = res.get_json()["data"].get("questions", [])
    return questions[0] if questions else None


def _build_answer_payload(question):
    """Build a valid answer payload for any question type."""
    qtype = question["question_type"]
    options = question.get("options", [])

    if qtype == "yes_no":
        if options:
            return {"question_id": question["id"], "selected_option_id": options[0]["id"]}
        return {"question_id": question["id"], "boolean_value": False}
    elif qtype in ("single_choice", "multiple_choice"):
        assert options, f"Choice question has no options: {question['id']}"
        return {"question_id": question["id"], "selected_option_id": options[0]["id"]}
    elif qtype == "number":
        return {"question_id": question["id"], "numeric_value": 3.0}
    else:
        return {"question_id": question["id"], "answer_text": "Test response text"}


def test_submit_yes_no_answer(client, registered_user, vomiting_assessment):
    """9. Submit a valid yes_no answer."""
    assessment_id = vomiting_assessment["id"]
    question = _get_first_question_for_assessment(
        client, registered_user["headers"], assessment_id
    )
    assert question is not None, "Should have questions for vomiting assessment"

    payload = _build_answer_payload(question)
    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=payload,
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["success"] is True
    answer = data["data"]
    assert answer["assessment_id"] == assessment_id
    assert answer["question_id"] == question["id"]
    assert "triggered_emergency" in answer


def test_submit_single_choice_answer(client, registered_user, vomiting_assessment):
    """10. Submit a valid single_choice answer using selected_option_id."""
    assessment_id = vomiting_assessment["id"]
    res_q = client.get("/api/v1/questions?category=Digestive")
    questions = res_q.get_json()["data"]["questions"]
    choice_q = next(
        (q for q in questions if q["question_type"] == "single_choice" and q["options"]),
        None,
    )
    if choice_q is None:
        pytest.skip("No single_choice Digestive question found in seed data")

    option = choice_q["options"][0]
    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json={"question_id": choice_q["id"], "selected_option_id": option["id"]},
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["selected_option_id"] == option["id"]


def test_submit_text_answer(client, registered_user, vomiting_assessment):
    """11. Submit a valid text answer."""
    assessment_id = vomiting_assessment["id"]
    res_q = client.get("/api/v1/questions?category=Digestive")
    questions = res_q.get_json()["data"]["questions"]
    text_q = next((q for q in questions if q["question_type"] == "text"), None)
    if text_q is None:
        pytest.skip("No text-type Digestive question in seed data")

    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json={"question_id": text_q["id"], "answer_text": "Several times, mostly bile"},
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["answer_text"] == "Several times, mostly bile"


def test_submit_numeric_answer(client, registered_user, vomiting_assessment):
    """12. Submit a valid numeric answer."""
    assessment_id = vomiting_assessment["id"]
    res_q = client.get("/api/v1/questions?category=Digestive")
    questions = res_q.get_json()["data"]["questions"]
    num_q = next((q for q in questions if q["question_type"] == "number"), None)
    if num_q is None:
        pytest.skip("No number-type Digestive question in seed data")

    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json={"question_id": num_q["id"], "numeric_value": 5.0},
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["numeric_value"] == 5.0


def test_duplicate_answer_rejected(client, registered_user, vomiting_assessment):
    """13. Submitting a duplicate answer for the same question returns 409."""
    assessment_id = vomiting_assessment["id"]
    question = _get_first_question_for_assessment(
        client, registered_user["headers"], assessment_id
    )
    assert question is not None

    payload = _build_answer_payload(question)
    r1 = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=payload,
    )
    assert r1.status_code == 201

    r2 = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=payload,
    )
    assert r2.status_code == 409
    assert r2.get_json()["success"] is False


def test_missing_question_id_rejected(client, registered_user, test_assessment):
    """14. Missing question_id returns 422."""
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=registered_user["headers"],
        json={"boolean_value": True},
    )
    assert res.status_code == 422


def test_no_answer_value_rejected(client, registered_user, vomiting_assessment):
    """15. Submitting with no answer value at all returns 422."""
    assessment_id = vomiting_assessment["id"]
    question = _get_first_question_for_assessment(
        client, registered_user["headers"], assessment_id
    )
    assert question is not None

    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json={"question_id": question["id"]},
    )
    assert res.status_code == 422


def test_invalid_question_uuid_rejected(client, registered_user, test_assessment):
    """16. Invalid question UUID format returns 422."""
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=registered_user["headers"],
        json={"question_id": "not-a-uuid", "boolean_value": True},
    )
    assert res.status_code == 422


def test_completed_assessment_rejects_new_answers(client, registered_user, test_pet):
    """17. Cannot submit answers to a completed assessment."""
    ass_res = client.post(
        f"/api/v1/pets/{test_pet['id']}/assessments",
        headers=registered_user["headers"],
    )
    assessment_id = ass_res.get_json()["data"]["id"]
    client.put(
        f"/api/v1/assessments/{assessment_id}",
        headers=registered_user["headers"],
        json={"status": "completed"},
    )

    res_q = client.get("/api/v1/questions?category=Digestive")
    questions = res_q.get_json()["data"]["questions"]
    if not questions:
        pytest.skip("No questions available")

    q = questions[0]
    payload = _build_answer_payload(q)
    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=payload,
    )
    assert res.status_code == 422
    body = res.get_json()
    assert "completed" in body.get("message", "").lower()


def test_submit_answer_wrong_user_rejected(client, second_user, test_assessment):
    """18. A different user cannot submit answers to another user's assessment."""
    res_q = client.get("/api/v1/questions")
    questions = res_q.get_json()["data"]["questions"]
    if not questions:
        pytest.skip("No questions available")

    q = questions[0]
    payload = _build_answer_payload(q)
    res = client.post(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=second_user["headers"],
        json=payload,
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# 19-24. GET /assessments/<id>/answers & /question-state
# ---------------------------------------------------------------------------

def test_get_answers_returns_list(client, registered_user, vomiting_assessment):
    """19. GET /answers returns all submitted answers with question details."""
    assessment_id = vomiting_assessment["id"]

    question = _get_first_question_for_assessment(
        client, registered_user["headers"], assessment_id
    )
    assert question is not None
    client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=_build_answer_payload(question),
    )

    res = client.get(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "answers" in data
    assert "total" in data
    assert data["total"] == 1
    ans = data["answers"][0]
    assert "question_id" in ans
    assert "triggered_emergency" in ans


def test_get_answers_wrong_user_forbidden(client, second_user, test_assessment):
    """20. Wrong user cannot retrieve another assessment's answers."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/answers",
        headers=second_user["headers"],
    )
    assert res.status_code == 403


def test_question_state_response_shape(client, registered_user, test_assessment):
    """21. GET /question-state returns required fields."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/question-state",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "questions" in data
    assert "progress" in data
    assert "emergency_flags" in data
    assert "is_ready_for_completion" in data
    assert "safety_message" in data
    progress = data["progress"]
    assert "answered" in progress
    assert "total_estimated" in progress
    assert "remaining_estimated" in progress


def test_question_state_emergency_flags_on_emergency_symptom(
    client, registered_user, breathing_assessment
):
    """22. Emergency flags present when emergency symptom attached."""
    res = client.get(
        f"/api/v1/assessments/{breathing_assessment['id']}/question-state",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data["emergency_flags"]) > 0, "Emergency symptom should produce flags"


def test_question_state_is_ready_false_initially(
    client, registered_user, vomiting_assessment
):
    """23. is_ready_for_completion is False before enough questions answered."""
    res = client.get(
        f"/api/v1/assessments/{vomiting_assessment['id']}/question-state",
        headers=registered_user["headers"],
    )
    data = res.get_json()["data"]
    if data["progress"]["total_estimated"] > 0:
        assert data["is_ready_for_completion"] is False


def test_question_state_wrong_user_forbidden(client, second_user, test_assessment):
    """24. Wrong user cannot see another assessment's question state."""
    res = client.get(
        f"/api/v1/assessments/{test_assessment['id']}/question-state",
        headers=second_user["headers"],
    )
    assert res.status_code == 403


# ---------------------------------------------------------------------------
# 25-26. Conditional Logic & Emergency Propagation
# ---------------------------------------------------------------------------

def test_emergency_answer_triggers_emergency_flag(
    client, registered_user, breathing_assessment
):
    """25 & 26. Submitting an emergency-flag answer raises emergency flag in state."""
    assessment_id = breathing_assessment["id"]

    q_res = client.get(
        f"/api/v1/assessments/{assessment_id}/next-questions",
        headers=registered_user["headers"],
    )
    questions = q_res.get_json()["data"]["questions"]
    assert questions, "Should have emergency questions for breathing assessment"

    target_q = None
    target_opt = None
    for q in questions:
        for opt in q.get("options", []):
            if opt["emergency_flag"]:
                target_q = q
                target_opt = opt
                break
        if target_q:
            break

    if not target_q:
        pytest.skip("No emergency-flag option in first batch of questions")

    res = client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json={
            "question_id": target_q["id"],
            "selected_option_id": target_opt["id"],
        },
    )
    assert res.status_code == 201
    answer = res.get_json()["data"]
    assert answer["triggered_emergency"] is True

    state_res = client.get(
        f"/api/v1/assessments/{assessment_id}/question-state",
        headers=registered_user["headers"],
    )
    state = state_res.get_json()["data"]
    assert len(state["emergency_flags"]) > 0


# ---------------------------------------------------------------------------
# 27. Species-Aware Question Selection
# ---------------------------------------------------------------------------

def test_species_aware_question_selection(client, second_user, second_user_pet):
    """27. Feline pet only receives species-appropriate questions."""
    ass_res = client.post(
        f"/api/v1/pets/{second_user_pet['id']}/assessments",
        headers=second_user["headers"],
    )
    assessment_id = ass_res.get_json()["data"]["id"]

    sym_res = client.get("/api/v1/symptoms?category=Skin")
    symptoms = sym_res.get_json()["data"]
    if symptoms:
        client.post(
            f"/api/v1/assessments/{assessment_id}/symptoms",
            headers=second_user["headers"],
            json={
                "symptom_id": symptoms[0]["id"],
                "severity": "mild",
                "duration_value": 1,
                "duration_unit": "days",
            },
        )

    res = client.get(
        f"/api/v1/assessments/{assessment_id}/next-questions",
        headers=second_user["headers"],
    )
    assert res.status_code == 200
    questions = res.get_json()["data"]["questions"]
    for q in questions:
        assert q.get("species") in (None, "Feline", "feline"), (
            f"Canine-only question returned for feline: {q['question_text']}"
        )


# ---------------------------------------------------------------------------
# 28. AI Payload includes Follow-Up Answers
# ---------------------------------------------------------------------------

def test_ai_payload_includes_follow_up_answers(
    client, registered_user, vomiting_assessment
):
    """28. AI-data endpoint payload includes follow_up_answers after submission."""
    assessment_id = vomiting_assessment["id"]

    question = _get_first_question_for_assessment(
        client, registered_user["headers"], assessment_id
    )
    assert question is not None
    client.post(
        f"/api/v1/assessments/{assessment_id}/answers",
        headers=registered_user["headers"],
        json=_build_answer_payload(question),
    )

    res = client.get(
        f"/api/v1/assessments/{assessment_id}/ai-data",
        headers=registered_user["headers"],
    )
    assert res.status_code == 200
    ai_input = res.get_json()["data"]["ai_input"]

    assert "follow_up_answers" in ai_input, (
        "AI payload must include follow_up_answers for Step 3 integration"
    )
    assert len(ai_input["follow_up_answers"]) >= 1
    ans = ai_input["follow_up_answers"][0]
    assert "question" in ans
    assert "category" in ans
    assert "priority" in ans
    assert "triggered_emergency" in ans
