"""Groq AI LLM Service for high-speed clinical pet care guidance.

Communicates with Groq's Chat Completions API with strict clinical safety guardrails,
species-specific contraindications, and seamless offline/mock fallback.
"""
import os
import json
import logging
import re
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from flask import current_app

logger = logging.getLogger(__name__)


class GroqService:
    """Interface to Groq AI LLM APIs with safety guardrails."""

    GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "openai/gpt-oss-120b"
    FALLBACK_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

    @classmethod
    def get_api_key(cls) -> str:
        """Retrieve configured Groq API key from app config or environment."""
        key = ""
        try:
            if current_app:
                key = current_app.config.get("GROQ_API_KEY", "")
        except RuntimeError:
            pass

        if not key:
            key = os.getenv("GROQ_API_KEY", "")

        return (key or "").strip()

    @classmethod
    def get_model(cls) -> str:
        """Retrieve Groq model name."""
        model = ""
        try:
            if current_app:
                model = current_app.config.get("GROQ_MODEL", "")
        except RuntimeError:
            pass

        if not model:
            model = os.getenv("GROQ_MODEL", "")

        return (model or cls.DEFAULT_MODEL).strip()

    @classmethod
    def is_available(cls) -> bool:
        """Check whether a valid non-placeholder Groq API key is present."""
        key = cls.get_api_key()
        if not key:
            return False
        # Verify it is not the default unedited template placeholder
        if key in ("your_groq_api_key_here", "gsk_your_key_here", "placeholder"):
            return False
        return len(key) >= 10

    @classmethod
    def call_chat_completion(
        cls,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
        timeout: int = 12,
    ) -> Optional[str]:
        """Execute chat completion request to Groq API.
        
        Returns response content string if successful, or None on failure.
        """
        api_key = cls.get_api_key()
        if not cls.is_available():
            logger.info("Groq API key not configured or using placeholder; skipping Groq LLM.")
            return None

        primary_model = cls.get_model()
        models_to_try = [primary_model]
        for m in cls.FALLBACK_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

        for model in models_to_try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                cls.GROQ_ENDPOINT,
                data=data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status == 200:
                        body = json.loads(response.read().decode("utf-8"))
                        choices = body.get("choices") or []
                        if choices and len(choices) > 0:
                            content = choices[0].get("message", {}).get("content", "")
                            return content
                    else:
                        logger.warning(f"Groq API returned HTTP status {response.status} for {model}")
            except urllib.error.HTTPError as e:
                err_body = ""
                try:
                    err_body = e.read().decode("utf-8")
                    logger.error(f"Groq API HTTPError {e.code} for {model}: {err_body}")
                except Exception:
                    logger.error(f"Groq API HTTPError {e.code} for {model}")
                # If model not found (404), try next model candidate in loop
                if e.code == 404 or "model_not_found" in err_body:
                    continue
                break
            except Exception as e:
                logger.error(f"Failed to communicate with Groq API for {model}: {str(e)}")
                break

        return None

    @classmethod
    def apply_guardrails_and_sanitize(
        cls,
        text: str,
        question: str,
        pet_name: str = "your pet",
        species: str = "pet",
    ) -> str:
        """Apply clinical safety guardrails, purge asterisks, and format cleanly."""
        if not text:
            return ""

        q_lower = (question or "").lower()
        t_lower = text.lower()

        # Guardrail 1: Human Medication Safety Guardrail
        med_triggers = [
            "paracetamol", "acetaminophen", "tylenol", "ibuprofen",
            "advil", "aspirin", "panadol", "motrin", "naproxen", "aleve"
        ]
        if any(m in q_lower for m in med_triggers):
            forbidden_words = ["do not", "never", "not safe", "toxic", "fatal", "strict warning", "danger", "harmful"]
            if not any(w in t_lower for w in forbidden_words):
                return (
                    f"STRICT SAFETY WARNING: Never give {pet_name} human pain relievers or fever medication. "
                    f"Acetaminophen (paracetamol/Tylenol) is fatal to cats even in trace amounts and causes acute liver destruction. "
                    f"Ibuprofen and human NSAIDs cause life-threatening kidney failure and severe stomach ulcers in pets. "
                    f"Contact an emergency veterinarian for safe, species-approved prescription pain relief."
                )

        # Guardrail 2: Induce Vomiting Safety Guardrail
        vomit_triggers = ["induce vomit", "make throw up", "make vomit", "hydrogen peroxide", "salt"]
        if any(v in q_lower for v in vomit_triggers):
            forbidden_words = ["do not", "never", "toxic", "danger", "harmful", "poison control"]
            if not any(w in t_lower for w in forbidden_words):
                return (
                    f"CRITICAL SAFETY WARNING: Do NOT attempt to induce vomiting in {pet_name} at home. "
                    f"Inducing vomiting causes chemical burns to the esophagus and fatal aspiration pneumonia. "
                    f"Immediately call ASPCA Animal Poison Control at (888) 426-4435 or Pet Poison Helpline at (855) 764-7661."
                )

        # Guardrail 3: Prescription Drug Dosage Guardrail
        dosage_triggers = ["dosage", "how much mg", "how many mg", "dose of", "how much amoxicillin", "how much prednisone"]
        if any(d in q_lower for d in dosage_triggers):
            if any(unit in t_lower for unit in ["mg/kg", "mg per", "give 5", "give 10", "give 25", "give 50", "give 100", "tablets"]):
                return (
                    f"PRESCRIPTION DOSAGE WARNING: Drug dosages must be calculated strictly by a licensed veterinarian "
                    f"based on {pet_name}'s species, exact weight, and organ health. Never guess drug dosages at home."
                )

        # Formatting Cleanup: Remove ALL asterisks (*, **, ***)
        cleaned = re.sub(r"\*+", "", text)

        # Remove markdown heading hashes (e.g. "### Heading" -> "Heading")
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)

        # Remove markdown horizontal rules (--- or ===)
        cleaned = re.sub(r"^[-=_]{3,}\s*$", "", cleaned, flags=re.MULTILINE)

        # Remove markdown table artifacts if model attempted tables
        cleaned = re.sub(r"\|", " ", cleaned)

        # Normalize multiple blank lines to a maximum of 2 newlines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        # Enforce brevity: If response is excessively long (> 200 words), cap cleanly at sentence boundary (<= 190 words)
        words = cleaned.split()
        if len(words) > 200:
            truncated = " ".join(words[:180])
            last_period = max(truncated.rfind("."), truncated.rfind("\n"))
            if last_period > 80:
                cleaned = truncated[:last_period + 1]
            else:
                cleaned = truncated + "..."

        return cleaned

    @classmethod
    def generate_pet_guidance(
        cls,
        question: str,
        pet_context: Optional[Dict[str, Any]] = None,
        assessment_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Generate high-quality supportive pet care guidance via Groq LLM with safety guardrails."""
        if not cls.is_available():
            return None

        p_ctx = pet_context or {}
        pet_name = p_ctx.get("name") or "your pet"
        species = p_ctx.get("species") or "pet"
        age = p_ctx.get("age") or "Unknown"
        breed = p_ctx.get("breed") or "Unknown"

        asmt_info = ""
        if assessment_context:
            symptoms = assessment_context.get("symptoms", [])
            risk_level = assessment_context.get("risk_level", "UNKNOWN")
            asmt_info = f"\nRecent Intake Context: Risk Level = {risk_level}, Reported Symptoms = {', '.join(symptoms) if symptoms else 'None'}."

        system_prompt = (
            f"You are VetVision AI, an expert, caring, and reliable veterinary health and pet care assistant. "
            f"You advise owners regarding their pets. "
            f"Context: Pet Name: {pet_name}, Species: {species}, Breed: {breed}, Age: {age}.{asmt_info}\n\n"
            f"CORE MISSION:\n"
            f"Provide direct, prompt, accurate, and comprehensive answers to ALL questions regarding pets and pet health. "
            f"Cover companion and daily pets including dogs, cats, birds, rabbits, hamsters, guinea pigs, reptiles, turtles, fish, and small mammals. "
            f"Address all domains: illness symptoms, diet and nutrition, safe vs. toxic foods, first aid, grooming, parasite control (fleas/ticks/worms), "
            f"dental hygiene, vaccinations, age-specific care (puppies/kittens/seniors), breed traits, and behavior/training.\n\n"
            f"CRITICAL OUT-OF-TOPIC GUARDRAIL:\n"
            f"If the user's inquiry is NOT about pets, domestic animals, wildlife, veterinary medicine, or animal care/health "
            f"(e.g., coding, computer programming, mathematics, general trivia, politics, sports, human medical diagnosis, human cooking recipes): "
            f"You MUST politely refuse to answer. State clearly that you are specialized exclusively in pet health, animal welfare, and veterinary guidance, "
            f"and kindly invite them to ask any question regarding pets and pet health.\n\n"
            f"FORMATTING GUIDELINES:\n"
            f"1. NO ASTERISKS: Do NOT use any asterisks (*) or double asterisks (**) anywhere. Write in clean plain text.\n"
            f"2. NO TABLES: Never use markdown table syntax or pipe characters (|). Use plain bullet points (with -) and clear section labels.\n"
            f"3. PROMPT & STRUCTURED: Give a direct answer immediately upfront, followed by practical details, tips, and when to seek veterinary attention.\n\n"
            f"CLINICAL SAFETY GUARDRAILS:\n"
            f"• Never prescribe medication dosages or definitively diagnose disease.\n"
            f"• STRICT CONTRAINDICATION: Never tell owners to give human medications (acetaminophen/paracetamol is fatal to cats; NSAIDs like ibuprofen cause acute kidney failure in pets).\n"
            f"• STRICT CONTRAINDICATION: Never tell owners to induce vomiting at home. Direct to ASPCA Poison Control (888-426-4435) or emergency vet.\n"
            f"• EMERGENCY OVERRIDE: For severe signs (breathing difficulty, pale/blue gums, collapse, active seizures, non-stop bleeding), instruct immediate emergency veterinary transport."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        raw_reply = cls.call_chat_completion(messages=messages, temperature=0.2, max_tokens=700)
        if not raw_reply:
            return None

        return cls.apply_guardrails_and_sanitize(
            text=raw_reply,
            question=question,
            pet_name=pet_name,
            species=species,
        )
