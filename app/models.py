"""Contains models for typing validation."""
from pydantic import AnyHttpUrl, BaseModel


class HttpUrl(BaseModel):
    """Model class that validates http urls, TLD not required.

    Attributes:
        url (AnyHttpUrl): Valid HTTP url.

    Args:
        url (str): Valid HTTP url string.

    Raises:
        pydantic.error_wrappers.ValidationError: If the url string is invalid
        or missing.

    Examples:
        Instantiate a new HttpUrl object with a string URL passed to the
        ``url`` argument.

        >>> from app.config import HttpUrl
        >>> server_url = HttpUrl(url="http://localhost:5000/log/")
        >>> server_url
        HttpUrl(url=AnyHttpUrl('http://localhost:5000/log/', scheme='http', host='localhost', host_type='int_domain', port='5000', path='/log/'))
        >>> server_url.url
        AnyHttpUrl('http://localhost:5000/log/', scheme='http', host='localhost', host_type='int_domain', port='5000', path='/log/')
        >>> str(server_url.url)
        'http://localhost:5000/log/'
        >>>
        >>> HttpUrl(url="readyornot")
        Traceback (most recent call last):
        File "<stdin>", line 1, in <module>
        File "pydantic/main.py", line 341, in pydantic.main.BaseModel.__init__
        pydantic.error_wrappers.ValidationError: 1 validation error for HttpUrl
        url
        invalid or missing URL scheme (type=value_error.url.scheme)
    """

    url: AnyHttpUrl
