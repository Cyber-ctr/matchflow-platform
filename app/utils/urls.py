from urllib.parse import urljoin, urlparse


def is_safe_url(target, host_url):
    if not target:
        return False
    ref = urlparse(urljoin(host_url, target))
    base = urlparse(host_url)
    return ref.scheme in {'http', 'https'} and ref.netloc == base.netloc
