from fastapi import FastAPI

app = FastAPI()


@app.get('/', summary='Главный эндпоинт', tags=['main'])
async def root():
    return 'Hello World'
