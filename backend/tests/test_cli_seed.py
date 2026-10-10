"""Tests for explicit database seeding CLI command (flask seed-db)."""
from app.extensions import db
from app.models.symptom import Symptom
from app.models.follow_up_question import FollowUpQuestion


def test_flask_seed_db_initial_and_repeat_execution(app):
    """Verify that 'flask seed-db' seeds vocabulary idempotently without record duplication."""
    runner = app.test_cli_runner()

    with app.app_context():
        # Clear existing symptoms and questions to test fresh initial seed
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

        assert Symptom.query.count() == 0
        assert FollowUpQuestion.query.count() == 0

    # 1. Initial execution of seed-db CLI
    res1 = runner.invoke(args=["seed-db"])
    assert res1.exit_code == 0
    assert "Database seeding completed successfully" in res1.output

    with app.app_context():
        sym_count_1 = Symptom.query.count()
        q_count_1 = FollowUpQuestion.query.count()
        assert sym_count_1 > 0, "Symptoms must be populated on initial seed"
        assert q_count_1 > 0, "Questions must be populated on initial seed"

    # 2. Repeat execution of seed-db CLI (Idempotency check)
    res2 = runner.invoke(args=["seed-db"])
    assert res2.exit_code == 0
    assert "Database seeding completed successfully" in res2.output
    assert "Clinical symptoms seeded: 0" in res2.output
    assert "Follow-up questions seeded: 0" in res2.output

    with app.app_context():
        sym_count_2 = Symptom.query.count()
        q_count_2 = FollowUpQuestion.query.count()
        assert sym_count_2 == sym_count_1, "Repeat seeding must not create duplicate symptoms"
        assert q_count_2 == q_count_1, "Repeat seeding must not create duplicate questions"
