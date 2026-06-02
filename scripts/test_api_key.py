#!/usr/bin/env python3
"""Smoke-test the deployed TPA API with an API key supplied by environment.

Usage:
    TPA_API_KEY=... python scripts/test_api_key.py

Optional:
    TPA_BASE_URL=https://... python scripts/test_api_key.py
"""

import os
import sys

import httpx

TPA_BASE_URL = os.getenv(
    "TPA_BASE_URL",
    "https://teaching-planning-assistant-production.up.railway.app",
).rstrip("/")
API_KEY = os.getenv("TPA_API_KEY", "")


def _require_api_key() -> None:
    if not API_KEY:
        print("❌ TPA_API_KEY is required. Export it before running this smoke script.")
        sys.exit(2)


def check_health() -> bool:
    print("Testing health endpoint...")
    response = httpx.get(f"{TPA_BASE_URL}/health", timeout=30)
    print(f"Health: {response.status_code} - {response.json()}")
    return response.status_code == 200


def check_curriculum_with_key() -> bool:
    print("\nTesting curriculum endpoint with API key...")
    response = httpx.get(
        f"{TPA_BASE_URL}/curriculum/niveles",
        headers={"X-API-Key": API_KEY},
        timeout=60,
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Curriculum response: {len(data)} courses")
        for course, subjects in list(data.items())[:3]:
            print(f"  - {course}: {', '.join(subjects[:3])}...")
        return True

    print(f"❌ Failed: {response.status_code}")
    print(response.text)
    return False


def check_content_generation() -> bool:
    print("\nTesting content generation (quiz)...")
    response = httpx.post(
        f"{TPA_BASE_URL}/api/v1/content/generate-quiz",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "oa_ids": ["MA01 OA 01"],
            "grade_level": "1° Básico",
            "subject": "Matemáticas",
            "num_questions": 3,
            "difficulty_level": "easy",
        },
        timeout=120,
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            quiz = data.get("quiz", {})
            print(f"✅ Quiz generated: {quiz.get('title', 'No title')}")
            print(f"   Questions: {len(quiz.get('questions', []))}")
            return True
        print(f"⚠️ Generation returned but not successful: {data.get('error')}")
        return False

    print(f"❌ Failed: {response.status_code}")
    print(response.text[:500])
    return False


def main() -> None:
    _require_api_key()

    print("=" * 50)
    print("Testing TPA API with provided API key")
    print("=" * 50)

    results = [
        ("Health", check_health()),
        ("Curriculum", check_curriculum_with_key()),
        ("Quiz Generation", check_content_generation()),
    ]

    print("\n" + "=" * 50)
    print("Results:")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")

    all_passed = all(result for _, result in results)
    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
