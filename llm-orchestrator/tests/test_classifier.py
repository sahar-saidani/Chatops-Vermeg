from intent.classifier import IntentClassifier
from intent.models import RequestMode


def test_realtime_examples_from_spec():
    classifier = IntentClassifier()

    cases = {
        "What version is installed on DEV?": ("installation", RequestMode.REAL_TIME, "DEV"),
        "Show failed Jenkins jobs": ("jenkins", RequestMode.REAL_TIME, None),
        "Current Oracle status": (None, RequestMode.REAL_TIME, None),  # oracle agent not implemented yet
        "Current infrastructure metrics": ("infrastructure", RequestMode.REAL_TIME, None),
        "Latest Git commits": ("git", RequestMode.REAL_TIME, None),
    }

    for text, (expected_agent, expected_mode, expected_env) in cases.items():
        intent = classifier.classify(text)
        assert intent.mode is expected_mode, text
        if expected_agent:
            assert expected_agent in intent.agent_keys, text
        assert intent.environment == expected_env, text


def test_historical_examples_from_spec():
    classifier = IntentClassifier()

    cases = {
        "This week's Jenkins failures": "jenkins",
        "Git activity during the last release": "git",
        "Security vulnerabilities this year": None,  # security agent not implemented yet
    }

    for text, expected_agent in cases.items():
        intent = classifier.classify(text)
        assert intent.mode is RequestMode.HISTORICAL, text
        if expected_agent:
            assert expected_agent in intent.agent_keys, text
        assert not intent.requires_agent_execution


def test_no_matching_agent_without_llm_fallback_returns_low_confidence():
    classifier = IntentClassifier()
    intent = classifier.classify("What's the weather like today?")
    assert intent.agent_keys == []
    assert intent.confidence == 0.0


def test_time_range_extraction():
    classifier = IntentClassifier()
    intent = classifier.classify("Oracle dumps imported last month for the jira board")
    assert intent.mode is RequestMode.HISTORICAL
    assert intent.time_range_days == 30
