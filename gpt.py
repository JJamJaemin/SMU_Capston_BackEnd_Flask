import base64
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

        # 정규표현식을 사용하여 괄호 안의 텍스트 추출
        extracted_text = re.search(r'\((.*?)\)', send_message).group(1)

        if extracted_text is None:
            extracted_text = "중립"

            response = {
                "message": send_message.replace('\n', ''),
                "emotion": extracted_text,
                "status": check_end
            }
            print(f'감정 없을 때 : {response}')

        else:
            # 괄호와 함께 텍스트 제거
            cleaned_message = re.sub(r'\(.*?\)', '', send_message)

            response = {
                "message": cleaned_message.replace('\n', ''),
                "emotion": extracted_text,
                "status": check_end
            }
            print(f'감정 있을 때 : {response}')

        return response
    else:
        check_end = 0
        print(gptmessage, check_end)
        check_end = 0

        # 정규표현식을 사용하여 괄호 안의 텍스트 추출
        extracted_text = re.search(r'\((.*?)\)', gptmessage).group(1)
        if extracted_text == '중립':
            extracted_text = 0
        elif extracted_text == '슬픔':
            extracted_text = 1
        elif extracted_text == '기쁨':
            extracted_text = 2
        elif extracted_text == '분노':
            extracted_text = 3

        if extracted_text is None:
            extracted_text = 0 # GPT감정 (중립)

            response = {
                "message": gptmessage.replace('\n', ''),
                "emotion": extracted_text,
                "status": check_end
            }
            print(f'감정 없을 때 : {response}')
        else:
            # 괄호와 함께 텍스트 제거
            cleaned_message = re.sub(r'\(.*?\)', '', gptmessage)

            response = {
                "message": cleaned_message.replace('\n', ''),
                "emotion": extracted_text,
                "status": check_end
            }
            print(f'감정 있을 때 : {response}')
        return response

def create_diary(thread_id, userid, count): #일기 만들기 함수
    user_info = app.ID_collection.find_one({"userId": userid})

    find_number = int((count-1) * 2)

    thread_messages = GPTclient.beta.threads.messages.list(thread_id)
    print(thread_messages.data[0].content[0].text.value)
    gptmessage = thread_messages.data[find_number].content[0].text.value
    if "일기:" in gptmessage:
        split_text = gptmessage.split("일기:")
        send_message = split_text[0].strip()
        check_end = 1

        # 일기 내용 추출
        diary_match = re.search(r'일기: (.+?)\n', gptmessage, re.DOTALL)
        if diary_match is None:
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
            base64_encoded_data = base64.b64encode(binary_data)
            # base64 데이터를 UTF-8 문자열로 디코딩
            base64_message = base64_encoded_data.decode('utf-8')
            print(base64_message)

            user_messages = []
            for i, message in enumerate(thread_messages):
                if i % 2 != 0:
                    for content in message.content:
                        formatted_message = content.text.value
                        user_messages.insert(0, formatted_message)

            print(user_messages)
            print(len(user_messages))

            # 중립 감정을 저장할 배열들
            text_emotion = []
            voice_emotion = []

            # 각 배열마다 중립 감정을 분리하여 저장
            for message in user_messages:
                text, voice = message.split('(')[1].split(')')[0].split(',')
                text_emotion.append(text.strip())
                voice_emotion.append(voice.strip())

            # 결과 출력
            print("text_emotion 배열:", text_emotion)
            print("voice_emotion 배열:", voice_emotion)
            today = datetime.now()
            diary_data = {
                'userId': userid,
                'date': today,
                'image': base64_message,
                'content': diary_content,
                'textEmotion': text_emotion,
                'speechEmotion': voice_emotion,
                'chatCount': len(user_messages)
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

                six_w_content_dict = json.loads(six_w_content)

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
                    json.dump(six_w_content_dict, json_file, ensure_ascii=False)

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

                # JSON 문자열을 딕셔너리로 변환
                future_schedule_dict = json.loads(future_schedule)
                if future_schedule_dict.get("날짜") != None and future_schedule_dict.get("일정") != None:
                    print(future_schedule_dict)

                    date = future_schedule_dict["날짜"]
                    content = future_schedule_dict["일정"]

                    print(f'미래 일정 : {date, content}')

                    #DB 미래 일정 추가
                    future_collection = app.db.future
                    future_data = {
                        'userId': userid,
                        'Date' : date,
                        'Content' : content
                    }

                    future_collection.insert_one(future_data)

                    print(future_schedule)
                else:
                    print("미래일정 형식이 맞지 않음")
            else:
                print("미래 일정 없음")
        else:
            print("일기 없음")

