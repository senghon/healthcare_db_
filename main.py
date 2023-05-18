# server_b.py
from fastapi import FastAPI
from sqlalchemy import create_engine, text
import openai
import os
import uvicorn
import pymssql

#uvicorn main:app --host 0.0.0.0 --port 8011
app = FastAPI()

#openai key
openai.api_key = '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'
# ##openai
def get_completion(prompt, model="gpt-3.5-turbo-0301"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.7, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

# DB 연결 설정
login_dta = {
    'server': 'localhost',
    # 'port': '1433',
    'database': 'efmain'
    # 'username': 'senghon',
    # 'password': 'yy5625'
}
# engine = create_engine(f"mssql+pymssql://{login_dta['username']}:{login_dta['password']}@{login_dta['server']}:{login_dta['port']}/{login_dta['database']}")
engine = create_engine(f"mssql+pymssql://{login_dta['server']}/{login_dta['database']}")

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
    

#환자 클릭시 개별 환자 정보 get
@app.get('/{patient_id}/{vsid}')
def patient_info(patient_id,vsid):
    prompt = f"""
    너는 '작업 명령'에 따라서 '작업 데이터'를 작업한 다음에 '결과 명령'에 따라서 '결과 포멧'에 맞춰서 결과물을 리턴해주면 돼.
    
    작업 목표 :
    수의사가 건강검진을 진행한 반려동물 건강검진 결과를 보호자에게 설명하는 리포트를 작성.

    작업 명령 :
    1. 너는 일종의 요약 작업을 진행 해야해\
    2. 작업을 진행하는 데이터의 종류는 수의사가 건강검진을 진행한 동물의 전자차트 내 SOAP 데이터야\
    3. SOAP중 S(subject)는 제외해야해. 수의사가 보호자로부터 문진한 내용은 요약에서 제외해.\
     3-1. 보통 차트데이터 구성은 S(subject)가 제일 위에 위치해. 이 부분이 보호자로부터 들은 환자 데이터이므로 작업에서 제외 해야해.\
     3-2. 보통 object,assesment,plan 데이터는 데이터마다 o),a),p) 혹은 o>,a>,p>로 구분점을 두고 있어.\
    4. 너는 이 데이터를 받아서 신체검사결과,혈액검사결과,영상검사결과,전체 결과 및 관리방안 카테고리로 요약해 줘야해.\
    
    결과 명령 :
    1. 구어체의 친절한 어조 사용.\
    2. 영문 용어,영어 용어,의학 용어는 쉬운 한글로 풀어서 설명.\
    3. 카테고리별로 이상이 없다면 이상이 없다고 말을 하면 돼. 억지로 채울 필요는 없어.\
    
    결과 포멧 :
    -
    신체검사 결과 : 
    혈액검사 결과 : 
    영상검사 결과 : 
    전체 결과 및 관리 방안 :
    -
    작업데이터 : '''{patient_subject(patient_id,vsid)}'''
    """
    examresult = {
        'subject' : patient_subject(patient_id,vsid),
        'chatgpt' : get_completion(prompt),
        'bloodtest' : paitent_bloodtest(patient_id,vsid)
    }
    return examresult

# ## patient blood test 결과 
def paitent_bloodtest(patient_id,vsid) :
    with engine.connect() as conn:
        bloodtest = []
        query = text(f"""
            SELECT hlbdesc,hlbresult,hlbunit
            FROM dbo.hlb
            WHERE hlbptid = '{patient_id}' AND hlbvsid = '{vsid}'
        """)
        result = conn.execute(query)
        if result:
            for i in result :
                bloodresult = {
                    'name' : i[0],
                    'result' : i[1],
                    'unit' : i[2]
                }
                bloodtest.append(bloodresult)
            return bloodtest
        else:
            return None

## patient subject 데이터 전송
def patient_subject(patient_id,vsid):
    with engine.connect() as conn:
        query = text(f"""
            SELECT hsetxtcont
            FROM dbo.hse
            WHERE hseptid = '{patient_id}' AND hsevsid = '{vsid}'
        """)
        result = conn.execute(query)
        row = result.fetchone()
        if row:
            return row[0].encode('ISO-8859-1').decode('cp949')
        else:
            return None

#find 함수 모음
def find_clid(ptclid):
    with engine.connect() as conn:
        query = text(f"""
            SELECT cllname
            FROM dbo.cl
            WHERE clid = '{ptclid}'
        """)
        result = conn.execute(query)
        row = result.fetchone()
        if row:
            return row[0].encode('ISO-8859-1').decode('cp949')
        else:
            return None

def find_brid(ptbrid):
    with engine.connect() as conn:
        query = text(f"""
            SELECT brdesc,brspid
            FROM dbo.br
            WHERE brid = '{ptbrid}'
        """)
        result = conn.execute(query)
        row = result.fetchone()
        if row:
            return [row[0].encode('ISO-8859-1').decode('cp949'),row[1]]
        else:
            return None

def find_staf(hplstf) :
    with engine.connect() as conn:
        query = text(f"""
            SELECT emname
            FROM dbo.em
            WHERE emcode = '{hplstf}'
        """)
        result = conn.execute(query)
        row = result.fetchone()
        if row:
            return row[0].encode('ISO-8859-1').decode('cp949')
        else:
            return None

def find_xid(ptxid):
    with engine.connect() as conn:
        query = text(f"""
            SELECT sxdesc FROM dbo.sx WHERE sxid = '{ptxid}'
        """)
        result = conn.execute(query)
        row = result.fetchone()
        if row:
            return row[0].encode('ISO-8859-1').decode('cp949').strip()
        else:
            return None
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)