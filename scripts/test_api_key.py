#!/usr/bin/env python3
import requests
import json

TPA_BASE_URL = "https://teaching-planning-assistant-production.up.railway.app"
API_KEY = "tpa_njoCspLGlxKP4LA7m_YddDFCCehfN9eECiQ-IaV2l1g"

def test_health():
    print("Testing health endpoint...")
    response = requests.get(f"{TPA_BASE_URL}/health", timeout=30)
    print(f"Health: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_curriculum_with_key():
    print("\nTesting curriculum endpoint with API key...")
    response = requests.get(
        f"{TPA_BASE_URL}/curriculum/niveles",
        headers={"X-API-Key": API_KEY},
        timeout=60
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Curriculum response: {len(data)} courses")
        for course, subjects in list(data.items())[:3]:
            print(f"  - {course}: {', '.join(subjects[:3])}...")
        return True
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)
        return False

def test_content_generation():
    print("\nTesting content generation (quiz)...")
    response = requests.post(
        f"{TPA_BASE_URL}/api/v1/content/generate-quiz",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "oa_ids": ["MA01 OA 01"],
            "grade_level": "1° Básico",
            "subject": "Matemáticas",
            "num_questions": 3,
            "difficulty_level": "easy"
        },
        timeout=120
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            quiz = data.get("quiz", {})
            print(f"✅ Quiz generated: {quiz.get('title', 'No title')}")
            print(f"   Questions: {len(quiz.get('questions', []))}")
            return True
        else:
            print(f"⚠️ Generation returned but not successful: {data.get('error')}")
            return False
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text[:500])
        return False

def main():
    print("=" * 50)
    print("Testing TPA API with new API key")
    print("=" * 50)
    
    results = []
    
    results.append(("Health", test_health()))
    results.append(("Curriculum", test_curriculum_with_key()))
    results.append(("Quiz Generation", test_content_generation()))
    
    print("\n" + "=" * 50)
    print("Results:")
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print("\n" + ("✅ All tests passed!" if all_passed else "❌ Some tests failed"))

if __name__ == "__main__":
    main()
