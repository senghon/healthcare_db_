from fastapi import FastAPI

app = FastAPI()

@app.get("/api/db")
def process_request():
    # DB에서 데이터 조회 등의 로직 수행
    data = {"message": "DB로부터 조회된 데이터입니다."}
    
    # 데이터 반환
    return data