import app
import time
def searchGPT(userid, threadid, text):
    userid = str(userid)
    # MongoDB에서 사용자의 GPT ID 가져오기
    # 사용자 정보 조회
    user_info = app.ID_collection.find_one({"userId": userid})

    if user_info:
        searchGPT = user_info.get("SearchGptID")  # 사용자의 GPT ID 반환

        print(searchGPT)

        # 메세지 만들기
        thread_message = app.GPTclient.beta.threads.messages.create(
            threadid,
            role="user",
            content=text
        )
        print(thread_message)
        # run id 만들기
        run = app.GPTclient.beta.threads.runs.create(
            thread_id=threadid,
            assistant_id=searchGPT
        )

        run_id = run.id

        # run 검색, 응답을 기다림, 만드는게 아니기에 주석 안해도 됨
        while True:
            run = app.GPTclient.beta.threads.runs.retrieve(
                thread_id=threadid,
                run_id=run_id
            )
            if run.status == "completed":
                break
            else:
                time.sleep(2)
        thread_messages = app.GPTclient.beta.threads.messages.list(threadid)
        gptmessage = thread_messages.data[0].content[0].text.value
        result = gptmessage.split("【")[0]

        if result is not None:
            response = {
                "answer": result
            }
        else:
            response = {
                "answer": gptmessage
            }

        return response
    else:
        response = {
            "messages": "해당 유저가 없음"
        }
        return response  # 사용자가 없을 경우 None 반환