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
from collections import OrderedDict

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
    print("퐁당의 대화: ", thread_messages.data[0].content[0].text.value)
    gptmessage = thread_messages.data[0].content[0].text.value
    if "일기:" in gptmessage:
        split_text = gptmessage.split("일기:")
        send_message = split_text[0].strip()
        check_end = 1

        # 정규표현식을 사용하여 괄호 안의 텍스트 추출
        extracted_text = re.search(r'\((.*?)\)', send_message)

        if extracted_text is None:
            extracted_text = 0

            response = {
                "message": send_message.replace('\n', ''),
                "emotion": extracted_text,
                "status": check_end
            }
            print(f'감정 없을 때 : {response}')

        else:
            extracted_text = re.search(r'\((.*?)\)', gptmessage).group(1)
            if extracted_text == '중립':
                extracted_text = 0
            elif extracted_text == '슬픔':
                extracted_text = 1
            elif extracted_text == '기쁨':
                extracted_text = 2
            elif extracted_text == '분노':
                extracted_text = 3
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
    conversation = []  # 대화내용을 저장할 리스트
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
                prompt=diary_content + '(말풍선 없는 카툰 스타일의 일러스트레이션)',
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
            ############################################
            absoluteEM = []
            abs_abs_count = []
            count = 0
            for i in text_emotion:
                if i == voice_emotion[count]:
                    absoluteEM.append(i)
                elif i == '중립' and voice_emotion[count] != '중립':
                    absoluteEM.append(voice_emotion[count])
                elif i == '불안':
                    absoluteEM.append('불안')
                elif i == '당황':
                    absoluteEM.append('당황')
                elif i == '상처':
                    absoluteEM.append('상처')
                elif i != '중립' and voice_emotion[count] == '중립':
                    absoluteEM.append(i)
                else:
                    absoluteEM.append('중립')
                count += 1
            print("최종감정", absoluteEM)

            # neutral = 0
            # angry = 0
            # sad = 0
            # happy = 0
            # embrassed = 0
            # hurt = 0
            # anxiety = 0
            # for i in absoluteEM:
            #     if i == '중립':
            #         neutral += 1
            #     elif i == '슬픔':
            #         sad += 1
            #     elif i == '분노':
            #         angry += 1
            #     elif i == '행복':
            #         happy += 1
            #     elif i == '불안':
            #         anxiety += 1
            #     elif i == '당황':
            #         embrassed += 1
            #     elif i == '상처':
            #         hurt += 1
            # abs_abs_count.append(neutral)
            # abs_abs_count.append(sad)
            # abs_abs_count.append(angry)
            # abs_abs_count.append(happy)
            # abs_abs_count.append(anxiety)
            # abs_abs_count.append(embrassed)
            # abs_abs_count.append(hurt)

            #피드백 생성
            thread_messages = GPTclient.beta.threads.messages.list(thread_id, order="asc")
            thread_messages_size = len(thread_messages.data)



            # 각 메시지를 출력하는 for문
            for i in range(thread_messages_size):
                feedgpt_message = thread_messages.data[i].content[0].text.value
                if "일기:" in feedgpt_message:
                    feedgpt_message = feedgpt_message.split("일기:")
                    feedgpt_message = feedgpt_message[0].strip()
                role = "user" if i % 2 == 0 else "answer"
                conversation.append({"role": role, "message": feedgpt_message})

            # JSON으로 변환
            conversation_json = json.dumps(conversation, ensure_ascii=False, indent=4)
            print(conversation_json)
            feedbackjson_folder = 'user_feedback'

            if not os.path.exists(feedbackjson_folder):
                os.makedirs(feedbackjson_folder)

            with open("user_feedback/feedback.json", "w", encoding="utf-8") as f:
                f.write(conversation_json)

            # 피드백 어시에 파일 업로드 하는 코드(공식 문서 보고 구현)
            vector_store = GPTclient.beta.vector_stores.create(name="feedback json")
            file_paths = glob.glob(os.path.join(feedbackjson_folder, '*'))  # 모든 파일 검색
            file_streams = [open(path, "rb") for path in file_paths]

            feedback_file_batch = GPTclient.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            # 업로드 후 파일 스트림 닫기
            for file_stream in file_streams:
                file_stream.close()

            print(feedback_file_batch.status)
            print(feedback_file_batch.file_counts)

            feedbackassistant = GPTclient.beta.assistants.update(
                assistant_id= "asst_Dem3ZGnGEXIlP2Bh8qBzf07P",
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            ####
            feedbackGptID = "asst_Dem3ZGnGEXIlP2Bh8qBzf07P"  # 사용자의 GPT ID 반환
            chat_thread = app.GPTclient.beta.threads.create().id

            # 메세지 만들기
            thread_message = app.GPTclient.beta.threads.messages.create(
                chat_thread,
                role="user",
                content= '시작'
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
            feedbackgptmessage = thread_messages.data[0].content[0].text.value
            clean_feedback = re.sub(r'【.*?】', '', feedbackgptmessage)
            #########################################################################
            ####################사용자 감정상태 변환######################################
            if not os.path.exists(feedbackjson_folder):
                os.makedirs(feedbackjson_folder)

            with open("user_feedback/feedback.json", "w", encoding="utf-8") as f:
                f.write(conversation_json)

            # 피드백 어시에 파일 업로드 하는 코드(공식 문서 보고 구현)
            vector_store = GPTclient.beta.vector_stores.create(name="feedback json")
            file_paths = glob.glob(os.path.join(feedbackjson_folder, '*'))  # 모든 파일 검색
            file_streams = [open(path, "rb") for path in file_paths]

            feedback_file_batch = GPTclient.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            # 업로드 후 파일 스트림 닫기
            for file_stream in file_streams:
                file_stream.close()

            print(feedback_file_batch.status)
            print(feedback_file_batch.file_counts)

            feedbackassistant = GPTclient.beta.assistants.update(
                assistant_id= "asst_Dem3ZGnGEXIlP2Bh8qBzf07P",
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            ####
            feedbackGptID = "asst_Dem3ZGnGEXIlP2Bh8qBzf07P"  # 사용자의 GPT ID 반환
            chat_thread = app.GPTclient.beta.threads.create().id

            # 메세지 만들기
            thread_message = app.GPTclient.beta.threads.messages.create(
                chat_thread,
                role="user",
                content= '시작'
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
            feedbackgptmessage = thread_messages.data[0].content[0].text.value
            clean_feedback = re.sub(r'【.*?】', '', feedbackgptmessage)

            ###############################감정 변화 측정 코드

            if not os.path.exists(feedbackjson_folder):
                os.makedirs(feedbackjson_folder)

            with open("user_feedback/feedback.json", "w", encoding="utf-8") as f:
                f.write(conversation_json)

            # 피드백 어시에 파일 업로드 하는 코드(공식 문서 보고 구현)
            vector_store = GPTclient.beta.vector_stores.create(name="feedback json")
            file_paths = glob.glob(os.path.join(feedbackjson_folder, '*'))  # 모든 파일 검색
            file_streams = [open(path, "rb") for path in file_paths]

            feedback_file_batch = GPTclient.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            # 업로드 후 파일 스트림 닫기
            for file_stream in file_streams:
                file_stream.close()

            print(feedback_file_batch.status)
            print(feedback_file_batch.file_counts)

            ChangeEmotionassistant = GPTclient.beta.assistants.update(
                assistant_id= "asst_pvypAltXQ1ma6SGXmuwewllj",
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            ####
            changeEmotionGptID = "asst_pvypAltXQ1ma6SGXmuwewllj"  # 사용자의 GPT ID 반환
            chat_thread = app.GPTclient.beta.threads.create().id

            # 메세지 만들기
            thread_message = app.GPTclient.beta.threads.messages.create(
                chat_thread,
                role="user",
                content= '알려줘'
            )
            print(thread_message)
            # run id 만들기
            run = app.GPTclient.beta.threads.runs.create(
                thread_id=chat_thread,
                assistant_id=changeEmotionGptID
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
            thread_messages2 = app.GPTclient.beta.threads.messages.list(chat_thread)
            find_thread_message = app.GPTclient.beta.threads.messages.list(thread_id, order="asc")
            Changegptmessage = thread_messages2.data[0].content[0].text.value
            clean_ChangeEmotion = re.sub(r'【.*?】', '', Changegptmessage)
            clean_ChangeEmotion = clean_ChangeEmotion.strip('[]').replace(' ','').split(',')

            ##########case 구별하기
            negative_emotions = ["불안", "상처", "슬픔", "당황", "분노"]
            positive_emotions = ["행복", "중립"]
            end_happy_emotion = ["행복"]
            end_neutral_emotion = ["중립"]



            AIChating = []
            small_emotions = []
            change_comment = [] #db에 넘겨줄 것

            #해당하는 comment들 db에 넘겨주는 것이 아님 -> change_comment에 append할 것
            case1_comment = [
                '저와의 이야기를 통해서 감정이 긍정적으로 변화하셔서 다행이에요!\n앞으로도 당신의 이야기를 들려주고 같이 이야기 해요!!',
            ]
            case2_comment = [
                '제가 별로 도움이 되지 못했어요ㅠㅠ\n제가 더 노력을 할테니 같이 이야기를 많이 해보아요!'
            ]
            change_happy_comment = [
                '제가 당신의 감정을 행복으로 이끌었어요!\n저의 피드백을 통해 감정이 행복으로 변화하셔서 너무 기쁩니다!'
            ]
            change_neutral_comment = [
                '제가 당신의 감정을 중립으로 이끌었어요!\n부정적인 감정을 덜어내고 마음의 평온을 찾으셔서 기뻐요!'
            ]

            same_happy_commnet = [
                "행복한 감정을 유지해서 너무 좋아요!\n앞으로도 제가 행복하게 해줄께요!!"
            ]

            same_neutral_comment = [
                "마음이 평온해서 다행이에요.\n마음의 평온도 좋지만 제가 행복하게 해드릴께요!!"
            ]

            print("첫 감정:", clean_ChangeEmotion[0])
            print("마지막 감정:", clean_ChangeEmotion[1])

            if clean_ChangeEmotion[0] in negative_emotions and clean_ChangeEmotion[1] in positive_emotions:
                print("case1")
                case = 1
                # 대 감정 변화에 대한 멘트(case가 1일 때)
                change_comment.append(case1_comment[0])

                # 종혜씨 요청
                print("종혜")
                print("종혜씨요청:", conversation)
                answer_messages = [entry['message'].split('(')[0].strip() for entry in conversation if
                                   entry['role'] == 'answer']
                print("챗봇만 대답:", answer_messages)
                ##########챗봇이 대화에서 준 피드백 가져오기

                for i in range(len(absoluteEM) - 1):
                    current = absoluteEM[i]
                    next = absoluteEM[i + 1]
                    if current in negative_emotions and next in positive_emotions:
                        print("피드백 도움이 있음")
                        print(f"{i}와 {i + 1}을 비교: {current} vs {next}")

                        find_number = int(i * 2) + 1
                        # print(find_number)

                        find_gpt_message = find_thread_message.data[find_number].content[0].text.value

                        extracted_text = re.search(r'\((.*?)\)', find_gpt_message)
                        if extracted_text:
                            find_gpt_message = re.sub(r'\(.*?\)', '', find_gpt_message)
                            AIChating.append(find_gpt_message)

                        else:
                            AIChating.append(find_gpt_message)

                        small_emotions.append([current,next])
                    else:
                        print("안 돌았을 때 : ",current,next)

                if small_emotions:
                    print("피드백 있을 때")

                    #소 감정 순서 고정, 거기에 맞는 comment
                    small_emotions = list(OrderedDict.fromkeys(tuple(sublist) for sublist in small_emotions))
                    small_emotions = [list(item) for item in small_emotions]
                    for i in range(len(small_emotions)):
                        if small_emotions[i][1] == '행복':
                            change_comment.append(change_happy_comment[0])
                        else:
                            change_comment.append(change_neutral_comment[0])

                    print('소 감정 : ',small_emotions)
                    print('넘겨줄 comment',change_comment)
            else:
                print("case2")
                # 종혜씨 요청
                print("종혜")
                print("종혜씨요청:", conversation)
                answer_messages = [entry['message'].split('(')[0].strip() for entry in conversation if entry['role'] == 'answer']
                print("챗봇만 대답:",answer_messages)
                case = 2
                # 대 감정 변화에 대한 멘트(case가 2일 때)
                if clean_ChangeEmotion[0] in positive_emotions and clean_ChangeEmotion[1] in end_happy_emotion:
                    change_comment.append(same_happy_commnet[0])
                elif clean_ChangeEmotion[0] in positive_emotions and clean_ChangeEmotion[1] in end_neutral_emotion:
                    change_comment.append(same_neutral_comment[0])
                else:
                    change_comment.append(case2_comment[0])

            today = datetime.now()
            diary_data = {
                'userId': userid,
                'date': today,
                'image': base64_message,
                'content': diary_content,
                'textEmotion': text_emotion,
                'speechEmotion': voice_emotion,
                'absEmotion': absoluteEM,
                'chatCount': len(user_messages),
                'feedback': clean_feedback,
                'changeEmotion': clean_ChangeEmotion, #[배열형태 감정 2개] #대 감정
                'smallEmotion': small_emotions, #대제목 밑에 들어갈 소 감정
                'AIChating': answer_messages, #공감 해준 메시지 찾은것
                'case': case, #case1 = 1 case2 = 2
                'changeComment': change_comment,  # 대 감정과 소 감정에 대한 코멘트들 배열형식 []
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
                    date_str = future_schedule_dict["날짜"]  # 예: "2024-05-10"
                    date = datetime.strptime(date_str, '%Y-%m-%d')  # 문자열을 datetime 객체로 변환
                    #date = future_schedule_dict["날짜"]
                    content = future_schedule_dict["일정"]

                    print(f'미래 일정 : {date, content}')

                    #DB 미래 일정 추가
                    future_collection = app.db.future
                    future_data = {
                        'userId': userid,
                        'date' : date,
                        'content' : content
                    }

                    future_collection.insert_one(future_data)

                    print(future_schedule)
                else:
                    print("미래일정 형식이 맞지 않음")
            else:
                print("미래 일정 없음")
        else:
            print("일기 없음")