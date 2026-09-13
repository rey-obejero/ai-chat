import json

from ai_chat.shared.exceptions import problem_response


def test_problem_response_matches_rfc9457_shape() -> None:
    response = problem_response(
        status_code=401,
        title="Not Authenticated",
        detail="No session",
        code="NOT_AUTHENTICATED",
        instance="/api/v1/me",
    )

    assert response.media_type == "application/problem+json"
    body = json.loads(response.body)
    assert body == {
        "type": "about:blank",
        "title": "Not Authenticated",
        "status": 401,
        "detail": "No session",
        "instance": "/api/v1/me",
        "code": "NOT_AUTHENTICATED",
    }
