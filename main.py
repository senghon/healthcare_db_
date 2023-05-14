# server_b.py
from fastapi import FastAPI
import uvicorn
import pymssql

#uvicorn server_b:app --host 0.0.0.0 --port 8010
app = FastAPI()

@app.get("/response")
async def response_from_b():
    return {"message": "This is a response from B 컴퓨터."}


@app.get("/get_table_count")
async def get_table_count():
    # B 컴퓨터의 MSSQL 데이터베이스에 연결
    with pymssql.connect(
        server="localhost",
        # user="데이터베이스_사용자명",
        # password="데이터베이스_비밀번호",
        database="efmain"
    ) as conn:
        with conn.cursor() as cursor:
            # 테이블 개수를 쿼리합니다.
            cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
            table_count = cursor.fetchone()[0]
    return {"table_count": table_count}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)