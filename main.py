# server_b.py
from fastapi import FastAPI
import uvicorn
import pymssql

#uvicorn server_b:app --host 0.0.0.0 --port 8010
app = FastAPI()

@app.get("/response")
async def response_from_b():
    return {"message": "This is a response from B 컴퓨터."}

##오늘의 건강검진 환자 불러오기
@app.get("/today_patients_list")
def today_patients_list():
    with engine.connect() as conn:
#         # dbo.hpl에서 hplptid, hplrdt,hplstf,hplvsid 추출
        query1 = text("""
            SELECT hplptid,hplrdt,hplstf,hplvsid
            FROM dbo.hpl
            WHERE CONVERT(date, hplrdt) = '2022-06-20' AND hplplid = 12000
        """)
        result1 = conn.execute(query1)
        rows1 = result1.fetchall()

        # dbo.pt에서 ptid, ptname, ptsxid, ptclid, ptbrid 추출
        pt_info = []
        for row in rows1:
            query2 = text(f"""
                SELECT ptid, ptname, ptsxid, ptclid, ptbrid
                FROM dbo.pt
                WHERE ptid = '{row[0]}'
            """)
            result2 = conn.execute(query2)
            row2 = result2.fetchone()
            pt_info.append({
                "ptid": row2[0],
                "ptname": row2[1].encode('ISO-8859-1').decode('cp949').strip(),
                "ptsxid": find_xid(row2[2]),
                "ptclid": find_clid(row2[3]),
                "ptbrid": find_brid(row2[4]),
                "hplrdt": str(row[1]), # datetime 객체를 str로 변환
                "emname":find_staf(row[2]),
                "vsid" : row[3] #visd는 row의 3번째에 위치.
            })

        return pt_info

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)