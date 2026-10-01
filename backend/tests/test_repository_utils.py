from app.routes.repositories import normalize_repository_url


def test_normalize_git_suffix():
    url = "https://github.com/saadfoda/AlbertaLakesSite.git"

    assert normalize_repository_url(url) == (
        "https://github.com/saadfoda/AlbertaLakesSite"
    )


def test_normalize_trailing_slash():
    url = "https://github.com/saadfoda/AlbertaLakesSite/"

    assert normalize_repository_url(url) == (
        "https://github.com/saadfoda/AlbertaLakesSite"
    )


def test_normalize_hostname_case():
    url = "https://GITHUB.COM/saadfoda/AlbertaLakesSite.git"

    assert normalize_repository_url(url) == (
        "https://github.com/saadfoda/AlbertaLakesSite"
    )