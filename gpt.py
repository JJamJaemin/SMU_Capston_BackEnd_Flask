from datetime import datetime

import apikey
import app
import time
import re
import json
import os
import glob
import requests
from openai import OpenAI

def download_image(url, file_path): #이미지 다운로드
    try:
        # 이미지 다운로드 요청 보내기
        response = requests.get(url)
        # 요청이 성공했는지 확인
        if response.status_code == 200:
            # 파일에 이미지 쓰기
            with open(file_path, 'wb') as file:
                file.write(response.content)
            print("이미지 다운로드 및 저장 완료")
        else:
            print("이미지 다운로드 실패:", response.status_code)
    except Exception as e:
        print("에러 발생:", e)

def read_image_as_binary(image_path): #이미지 읽기
    with open(image_path, 'rb') as image_file:
        binary_data = image_file.read()
    return binary_data

GPTclient = OpenAI(
            api_key=apikey.api_key
        )
def sendGPT(userid, thread_id, text): #챗봇 대화 함수
    userid = str(userid)
    # MongoDB에서 사용자의 GPT ID 가져오기
    # 사용자 정보 조회

    user_info = app.ID_collection.find_one({"userId": userid})

    if user_info:
        gptid = user_info.get("GptID")  # 사용자의 GPT ID 반환
    else:
        return None  # 사용자가 없을 경우 None 반환

    # 메세지 만들기
    thread_message = GPTclient.beta.threads.messages.create(
        thread_id,
        role="user",
        content= text
    )
    # run id 만들기
    run = GPTclient.beta.threads.runs.create(
        thread_id = thread_id,
        assistant_id = gptid
    )

    run_id = run.id

    # run 검색, 응답을 기다림, 만드는게 아니기에 주석 안해도 됨
    while True:
        run = GPTclient.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        if run.status == "completed":
            break
        else:
            time.sleep(2)
    thread_messages = GPTclient.beta.threads.messages.list(thread_id)
    print(thread_messages.data[0].content[0].text.value)
    gptmessage = thread_messages.data[0].content[0].text.value
    if "일기:" in gptmessage:
        split_text = gptmessage.split("일기:")
        send_message = split_text[0].strip()
        check_end = 1

        return send_message, check_end
    else:
        check_end = 0
        print(gptmessage, check_end)
        return gptmessage, check_end

def create_diary(thread_id, userid): #일기 만들기 함수
    user_info = app.ID_collection.find_one({"userId": userid})

    thread_messages = GPTclient.beta.threads.messages.list(thread_id)
    print(thread_messages.data[0].content[0].text.value)
    gptmessage = thread_messages.data[0].content[0].text.value
    if "일기:" in gptmessage:
        split_text = gptmessage.split("일기:")
        send_message = split_text[0].strip()
        check_end = 1

        # 일기 내용 추출
        diary_match = re.search(r'일기:(.+?)\n', gptmessage, re.DOTALL)
        if diary_match:
            diary_content = diary_match.group(1).strip()
            print(diary_content)
            db = app.client.SMU_Capston  # 데이터베이스 이름
            Diary_collection = db.diary  # ID 컬렉션.


            # 이미지 만드는거
            diary_image = GPTclient.images.generate(
                model="dall-e-3",
                prompt=diary_content,
                n=1,
                size="1024x1024"
            )

            print(diary_image.data[0].url)
            file_path = "image/download.png" #todo 나중에 여러사용자가 사용할 경우 충돌 가능성 있음
            download_image(diary_image.data[0].url, file_path)
            binary_data = read_image_as_binary(file_path)
            print(binary_data)

            diary_data = {
                'userID': userid,
                'Date': str(datetime.now().date()),
                'image': binary_data,
                'content': diary_content,
                'textEmotion': 'textemotion',
                'speechEmotion': 'speechemotion'
            }
            result = Diary_collection.insert_one(diary_data)
            print('일기 저장완료:', result.inserted_id)
            # 육하 원칙 추출
            six_w_match = re.search(r'육하원칙:\s*({.*?})', gptmessage, re.DOTALL)

            if six_w_match is None:
                six_w_match = re.search(r'육하원칙:\n({.*?})\n', gptmessage, re.DOTALL)
                if six_w_match is None:
                    six_w_match = re.search(r'육하원칙:({.*?})\n', gptmessage, re.DOTALL)

            if six_w_match:
                six_w_content = six_w_match.group(1)

                # 백슬래시 및 개행 문자 제거(대충 해봄)
                # six_w_content = six_w_content.replace('\\', '').replace('\n', '')

                print(six_w_content)

                # user_json 폴더 경로
                json_folder = f'{userid}_json'

                # user_json 폴더가 없다면 생성
                if not os.path.exists(json_folder):
                    os.makedirs(json_folder)

                # 파일 경로 설정
                json_folder = f"{userid}_json"
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_file_path = os.path.join(json_folder, f'six_w_principles_{current_time}.json')

                with open(json_file_path, 'w') as json_file:
                    json.dump(six_w_content, json_file, ensure_ascii=False)

                # 검색 어시에 파일 업로드 하는 코드(공식 문서 보고 구현)
                vector_store = GPTclient.beta.vector_stores.create(name="search json")

                file_paths = glob.glob(os.path.join(json_folder, '*'))  # 모든 파일 검색
                file_streams = [open(path, "rb") for path in file_paths]

                file_batch = GPTclient.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id, files=file_streams
                )
                # 업로드 후 파일 스트림 닫기
                for file_stream in file_streams:
                    file_stream.close()

                print(file_batch.status)
                print(file_batch.file_counts)

                assistant = GPTclient.beta.assistants.update(
                    assistant_id= user_info.get("SearchGptID"),
                    tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}},
                )
            else:
                print("육하원칙 없음")

            # 미래 일정 추출
            future_schedule_match = re.search(r'미래일정:\s*({.*?})', gptmessage, re.DOTALL)
            if future_schedule_match:
                future_schedule = future_schedule_match.group(1)
                print(future_schedule)
            else:
                print("미래 일정 없음")
        else:
            print("일기 없음")

