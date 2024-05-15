import time
import app

def feedbackGPT(userid, month_max_emotion): #챗봇 대화 함수
    userid = str(userid)
    # MongoDB에서 사용자의 GPT ID 가져오기
    # 사용자 정보 조회

    user_info = app.ID_collection.find_one({"userId": userid})

    if user_info:
        feedbackGptID = "asst_u4OwoVSVT2sF86jvmZ9qLLYx"  # 사용자의 GPT ID 반환
        chat_thread = app.GPTclient.beta.threads.create().id

        # 메세지 만들기
        thread_message = app.GPTclient.beta.threads.messages.create(
            chat_thread,
            role="user",
            content= month_max_emotion
        )
        print(thread_message)
        # run id 만들기
        run = app.GPTclient.beta.threads.runs.create(
            thread_id=chat_thread,
            assistant_id=feedbackGptID
        )

        run_id = run.id

        # run 검색, 응답을 기다림, 만드는게 아니기에 주석 안해도 됨
        while True:
            run = app.GPTclient.beta.threads.runs.retrieve(
                thread_id=chat_thread,
                run_id=run_id
            )
            if run.status == "completed":
                break
            else:
                time.sleep(2)
        thread_messages = app.GPTclient.beta.threads.messages.list(chat_thread)
        gptmessage = thread_messages.data[0].content[0].text.value

        response = {
            "feedback" : gptmessage
        }

        return response, 200
    else:
        response = {
            "messages" : "해당 유저가 없음"
        }
        return response, 400 # 사용자가 없을 경우 None 반환