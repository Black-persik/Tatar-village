import requests

# Получение токена
url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'RqUID': 'b15dc234-3503-40d5-ac09-c25453176832',
    'Authorization': 'Basic N2NlY2E4NjMtYjFhMi00N2MxLTkwYjAtNzc3NjVmOWVkY2U5OjA3OGE1NGEzLTRlMjctNDMzMi05N2VlLWEyMWVkMzk5OTMyNQ=='
}
payload = {
    'scope': 'GIGACHAT_API_PERS'
}

response_for_token = requests.post(url, headers=headers, data=payload, verify=False)

# Проверяем, что токен получен успешно
if response_for_token.status_code != 200:
    print(f"Ошибка получения токена: {response_for_token.status_code}")
    print(response_for_token.text)
    exit()

try:
    access_token = response_for_token.json()['access_token']
    print(f"Токен получен успешно: {access_token[:20]}...")
except KeyError:
    print("Ошибка: токен не найден в ответе")
    print(response_for_token.json())
    exit()


def get_answer(question: str, user_answer: str) -> str:
    """
    Получает ответ от GigaChat API с проверкой ответа пользователя.
    """
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    # Формируем промпт для проверки ответа
    system_prompt = f"""Представь, что ты добрая и вежливая  бабушка, которая говорит ТОЛЬКО ПО-РУССКИ!!!.
    Пользователю был задан вопрос: '{question}'
    Пользователь ответил: '{user_answer}'
	Если пользователь правильно ответил на вопрос - похвали пользователя.
	Если пользователь ответил не по теме - вежливо укажи на его ошибки.
    Будь доброй и поддерживающей. НЕ ОТВЕЧАЙ ПО_ТАТАРСКИ!!!
    Отвечай сплошным текстом - не отвечай по пунктам.
    Отвечай не больше двух предложений. Старайся ответь кратко и ясно
    Выводи только одну фразу!

    """


    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"  # Используем полученный токен
    }

    payload = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Ответ: '{user_answer}'"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500

    }

    try:
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)

        # Проверяем статус ответа
        if resp.status_code != 200:
            return f"Ошибка API: {resp.status_code} - {resp.text}"

        # Извлекаем ответ
        answer = resp.json()['choices'][0]['message']['content']
        from gradio_client import Client

        client = Client("https://v2.api.translate.tatar/")
        total_answer = client.predict(
            lang="rus2tat",
            text=answer,
            api_name="/translate_interface"
        )
        return total_answer

    except requests.exceptions.RequestException as e:
        return f"Ошибка сети: {e}"
    except KeyError as e:
        return f"Ошибка парсинга ответа: {e}"
    except Exception as e:
        return f"Неожиданная ошибка: {e}"
