from openai import OpenAI
from .settings import settings
TOKEN = settings.openAI_API_KEY

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=TOKEN,
)


async def create_answer(message):
    completion = client.chat.completions.create(
      model="deepseek/deepseek-r1:free",
      messages=[
        {
            "role": "user",
            "content": f'''
            Помоги разобраться с заданием. Его текст звучит так: {message}
            У меня есть несколько вопросов:
            1. Посоветуй литературу или статьи, где можно изучить основы этой темы.
            2. Дай идеи для решения: какие подходы/алгоритмы уместны, на что обратить внимание.
            3. Если это задание требует программирования, покажи каркас кода (например, структуру классов или функций без реализации логики), но не готовый код.
            4. Не давай полное решение — хочу разобраться сам.
            5. Можешь предложить контрольные вопросы, чтобы проверить мое понимание.
            6. Как бы ты разбил эту задачу на подзадачи? Хочу понять с чего начать.
            '''
        }
      ]
    )
    return completion.choices[0].message.content