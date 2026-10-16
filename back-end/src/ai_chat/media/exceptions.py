from ai_chat.shared.exceptions import AppError


class MediaFetchError(AppError):
    """A media fetch failed a guard or the origin did not cooperate.

    The route converts this to a bare ``502`` (no body): the caller is an
    ``<img>`` element, and a problem+json document would only paint a broken
    image anyway.
    """

    status_code = 502
    code = "MEDIA_FETCH_FAILED"
    title = "Bad Gateway"
