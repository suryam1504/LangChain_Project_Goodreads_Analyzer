import requests

def get_books(user_id: str, shelf: str = "read"):
    # shelf can be "read", "currently-reading", "to-read"
    url = f"https://api.piratereads.com/{user_id}/{shelf}"
    response = requests.get(url)
    return response.json()

def get_all_books(user_id: str):
    read = get_books(user_id, "read")
    reading = get_books(user_id, "currently-reading")
    to_read = get_books(user_id, "to-read")
    return {"read": read, "currently_reading": reading, "to_read": to_read}