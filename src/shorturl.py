import hashlib

def shorten_url_hash(url: str):
    """
    Функция для создания короткого url
    :param url: исходный url
    :return: короткий url
    """
    hash_creator = hashlib.sha256()
    hash_creator.update(url.encode())
    url_hash = hash_creator.hexdigest()[:6]
    return url_hash

