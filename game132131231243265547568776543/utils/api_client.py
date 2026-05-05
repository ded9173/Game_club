import requests

BASE_URL = "http://localhost:4444/TransferSimulator/"
FALLBACK_URL = "http://prb.sylas.ru/TransferSimulator/"

def get_client_full_name():
    """
    Получает ФИО клиента через GET-запрос.
    :return: str или None
    """
    for url in [BASE_URL + "fullName", FALLBACK_URL + "fullName"]:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("value", "").strip()
            elif response.status_code == 500:
                print(f"❌ Ошибка 500 при запросе к {url}")
                print("Срочно обратитесь к главному эксперту!")
                return None
        except Exception as e:
            print(f"Не удалось подключиться к {url}: {e}")
            continue
    return None