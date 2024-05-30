import os
import torch
from datetime import datetime, timedelta
import feedback
from werkzeug.datastructures import FileStorage
from flask import Flask, request, url_for, session, redirect, jsonify
from flask_restx import Api, Resource,fields, reqparse #swagger 명세서
from pymongo import collection

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import diary
from emotion_model import prediction,pre_prediction
from kobert import load_and_predict
import search
import gpt
import apikey
from openai import OpenAI
import json


import emotion_count
#MongoDB 연결
uri = "mongodb+srv://qqqaaaccc:0MgyTiCM067afKHj@jaemin.jyhcm0g.mongodb.net/?retryWrites=true&w=majority&appName=Jaemin"
# uri = "mongodb+srv://qqqaaaccc:LTcnsxc5byZUlWvg@japanmongo.wowxzoi.mongodb.net/?retryWrites=true&w=majority&appName=japanmongo"
# Create a new client and connect to the server #몽고 DB 클라이언트
#client = MongoClient(uri, server_api=ServerApi('1'))
client = MongoClient('mongodb://jaemin:4869@13.124.22.141', 27017)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client.SMU_Capston  # 데이터베이스 이름
ID_collection = db.users  # ID 컬렉션.

GPTclient = OpenAI(
            api_key=apikey.api_key
        )

app = Flask(__name__)

                                    ######Swagger######

#Swagger 명세서 만들기 경로 설정
api = Api(app, version='1.0', title='API 문서', description='Swagger 문서', doc="/a")
swagger_api = api.namespace('test', description='조회 API')
login_api = api.namespace('login', description='카카오 로그인 / 회원가입 API' )
Create_Chatroom_api = api.namespace('Create_Chatroom', description='일기 채팅방 만들기')
Create_Diary_api = api.namespace('Create_Diary_api', description='일기,육하원칙,이미지 생성하기')
Send_Message_Dairy_api = api.namespace('Send_Message_Dairy', description='Gpt에게 메시지 보내고 받기')
userinfo_api = api.namespace('userinfo', description='몽고DB에 저장되어 있는 사용자 데이터')
Search_Diary_api = api.namespace('Search_Diary_api', description='일기 가져오기')
Count_Month_Emotion_api = api.namespace('Count_Month_Emotion', description='한달 감정 카운트')
get_future_api = api.namespace('get_future_api', description='미래 일정 가져오기')
month_feedback_api = api.namespace('month_feedback_api', description='월 피드백 api')
Search_gpt_api = api.namespace('Search_gpt_api', description='사용자의 경험 검색 api')
Set_weight_api = api.namespace('set_weight_api', description='사용자별 가중치 설정 api')
#사용자 정보 모델 정의
user_model = api.model('User', {
    'userId': fields.String(required=True, description='User ID'),
    'nickname': fields.String(required=True, description='User Nickname')
})
#채팅방 생성 모델
chat_thread = api.model('ChatThread', {
    'userId': fields.String(required=True, description='User ID')
})
#sendmessage response
send_message_response = api.model('SendMessageResponse', {
    "message": fields.String("안녕하세요! 오늘은 어떤 일이 있었나요? ~~~",description='GPT 대답'),
    'emotion': fields.Integer(0, description='GPT 감정 (즉 TTS 감정)'),
    'status': fields.Integer(0,description='0이면 대화 진행중 1이면 일기 작성 버튼 활성화 요청')
})
# 채팅방 생성 응답 모델
chatroom_response_model = api.model('ChatroomResponse', {
    'chat_thread': fields.String('thread_h1oNWi9nCUKJWULFGt1oJJYT',description="채팅방의 고유 ID"),
    'message': fields.String("오늘 하루는 어땟어?",description='챗봇이 처음에 말거는 메시지'),
    'emotion': fields.Integer(0, description='0이면 중립 1이면 ~~~')
})
# 사용자 없음 응답 모델
user_not_found_model = api.model('UserNotFoundResponse', {
    'message': fields.String('error', description="에러 메시지")
})
#유저 정보 모델
user_info = api.model('UserInfo', {
    'userId': fields.String(required=True, description='User ID')
})
#######일기 생성 모델#######
diary_info = api.model('DiaryInfo', {
    'threadId': fields.String(required=True, description='threadID'),
    'userId': fields.String(required=True, description='userID'),
    'count': fields.Integer(required=True, description='count')
})
#
create_diary_response = api.model('CreateDiaryResponse', {
    'message': fields.String("일기 생성 완료",description='일기 생성 완료')

})
# Diary 모델 정의 (Swagger 문서에 사용됨)
diary_model = api.model('Diary', {
    'userId': fields.String(required=True, description='userId'),
    'date': fields.String("None",required=True, description='The diary date'),
    'month': fields.String("None",required=True, description='The diary month'),
    'limit': fields.String("None",required=True, description='Current?')
})
## Diary 불러오기 모델 response
search_diary_response = api.model('SearchDiaryResponse', {
    'userId': fields.String("3472769887", description='유저 ID'),
    'date': fields.String("2024-05-12", description='날짜'),
    'image': fields.String("base64형식 이미지 데이터", description='그림일기 이미지 데이터'),
    'content': fields.String("일기내용 오늘 무슨일이 있었당", description='일기내용'),
    'textEmotion': fields.String("",description='텍스트 감정 배열 형식'),
    'speechEmotion': fields.String("",description='음성 감정 배열 형식'),
    'absEmotion': fields.String("",description='최종 감정 배열 형식'),
    'chatCount': fields.Integer(7, description='채팅 갯수'),
    'feedback': fields.String("피드백 내용 ~~", description='피드백 어시AI가 주는 피드백'),
    'changeEmotion': fields.String("[슬픔,행복]",description='사건의 감정과 대화 최종 감정'),
    'small_emotion': fields.String("[[감정,감정]]", description='대 감정 밑에 들어갈 소 감정'),
    'AIChating': fields.String("['챗봇의 답변이 들어있습니다. 여러개도 있을 수 있음']",description='챗봇의 의미있는 답변'),
    'case': fields.Integer(1, description='1or2 로 1은 case 1,  2는 case2')
})
#한달 감정 카운트
month_count_model = api.model('MonthCountModel', {
    'userId': fields.String(required=True, description='userId'),
    'month': fields.String(required=True, description='month')
})
#한달 감정 카운트 response
month_count_response = api.model('MonthCountResponse', {
    "textCount": fields.String("배열 형식[3,2,1,0,0,0]",description='한달치 텍스트 감정 카운트 배열 neutral sad angry happy anxiety embarrassed hurt'),
    "speechCount": fields.String("배열 형식[1,2,3,0,0,0]", description='한달치 음성 감정 카운트 배열 neutral sad angry happy anxiety embarrassed hurt'),
    "absTextCount": fields.String("배열 형식[2,2,2,0,0,0]", description='한달치 최종 감정 카운트 배열 neutral sad angry happy anxiety embarrassed hurt'),
    "month_max_emotion": fields.String("배열 형식[분노]", description='한달에 나오는 최종 감정')
})
month_feedback_model = api.model('month_feedback_model', {
    'userId': fields.String(required=True, description='userId'),
    #'month_max_emotion': fields.String(required=True, description='month_max_emotion'),
    'emotion_list': fields.List(fields.String, required=False, description='Feedback list')
})

month_feedback_response = api.model('month_feedback_response', {
    'feedback': fields.String("이번달은 화가 많으시군요",description='한달 감정의 피드백')
})
#future 미래일정 불러오기 response
get_future_response = api.model('get_future_response', {
    "content": fields.String("데이터분석 자격증 시험",description='미래 일정 내용'),
    "date": fields.String("2024-05-12",description='미래 일정 날짜')
})
##gpt 메시지 보내기
file_upload = api.parser()
file_upload.add_argument('fileTest', type=FileStorage, location='files', required=True, help='음성 파일')
file_upload.add_argument('content', type=str, required=True, location='form', help='메시지 내용')
file_upload.add_argument('threadid', type=str, required=True, location='form', help='쓰레드 아이디')
file_upload.add_argument('userid', type=str, required=True, location='form', help='사용자 아이디')
file_upload.add_argument('weight', type=float, required=True, location='form', help='사용자 가중치')
#사용자 가중치 조절
user_weight_file_upload = api.parser()
user_weight_file_upload.add_argument('userid', type=str, required=True, location='form', help='사용자 아이디')
user_weight_file_upload.add_argument('file1', type=FileStorage, location='files', required=True, help='음성 파일1')
user_weight_file_upload.add_argument('file2', type=FileStorage, location='files', required=True, help='음성 파일2')
user_weight_file_upload.add_argument('file3', type=FileStorage, location='files', required=True, help='음성 파일3')
user_weight_file_upload.add_argument('file4', type=FileStorage, location='files', required=True, help='음성 파일4')
user_weight_file_upload.add_argument('file5', type=FileStorage, location='files', required=True, help='음성 파일5')
#가중치 조절 완료 response
Set_weight_response = api.model('set_weight_response', {
    "message": fields.String("가중치 조정이 완료되었습니다!")
})
#search gpt 모델
search_message_model = api.model('search_message_model', {
    "userId": fields.String(required=True, description='userId'),
    "threadId": fields.String(required=True, description='threadId'),
    "text": fields.String(required=True, description='text')
})
#search gpt response
search_gpt_response = api.model('search_message_response', {
    "answer": fields.String('어제 재민이랑 데이터 분석 공부를 했습니다~~~', description='search 어시의 대답')
})
# API 리소스
###############
#여기 부터 API
@login_api.route('/receive_user_info', methods=['POST']) #카카오 로그인 API (사용자X mongoDB 사용자 테이블 추가)
class receive_user_info(Resource):
    @login_api.expect(user_model, validate=True)
    @login_api.response(200, 'User added successfully')
    @login_api.response(400, 'User already exists')
    def post(self):
        user_info = request.get_json()
        print('Received user info:', user_info)

        # MongoDB에 이미 존재하는지 여부 확인
        existing_user = ID_collection.find_one({'userId': user_info['userId']})
        if existing_user:
            return {'message': 'User already exists in MongoDB'}, 400  # 이미 존재하는 사용자인 경우 클라이언트에게 에러 응답을 전송
        #유저별 GPT

        my_assistant = GPTclient.beta.assistants.create( # GPT 어시스턴트 생성
            instructions="너는 일기를 작성해 주는 AI야. 일기에 필요한 정보는 사용자와의 대화를 통해 누가ex(나와 친구), 언제ex(오늘(2024-5-12), 어디서ex(상명대학교에서), 무엇을ex(싸움을), 어떻게(말로), 왜(의견이 맞지 않아서) 처럼 육하원칙으로 너가 정보를 얻을거야. 오늘의 날짜는 현재 한국의 날짜이다. 사용자에게 정보를 얻어내기 위해 질문을 유도하면 돼. 텍스트 감정은 내가 다른 ai모델을 이용해서 얻은 나의 문장에 대한 감정이고 음성 감정은 문자을 말로 했을 때 측정된 감정이야. 나의 감정을 (텍스트 감정, 음성 감정) 이렇게 보내줄거야  ()안에 텍스트 감정은 상황에 대해서 피드백 해주고, 음성 감정은 예를들어 목소리가 안좋아보이시네요? 라고 하면서 목소리에 대해서 피드백을 해줘 너가 대답할때 너의 감정도 () 안에 넣어서 보여줘 대신 너는 감정 1개만 보여줘 대신 너는 중립, 슬픔, 기쁨, 분노 4가지 감정 중 1개만 넣어줘 육하원칙의 데이터를 모두 확보하면 대화를 끝내줘 너가 일기를 작성하는 AI라는건 숨기고 친구처럼 행동해줘 육하원칙 데이터를 얻기위해서 너무 직접적으로는 물어보지 말아줘 육하원칙 데이터를 모두 확보하면 대화를 끝내고 대화 내용을 바탕으로 일기를 생성해줘 그리고 육하원칙 내용이 들어간 Json형식으로 정리해줘 대화중에 미래에 대한 일정이 있는거 같으면 너가 얻은 데이터로 캘린더에 추가할거야 나한테 자세하게 질문을 해서 정확한 날짜와 시간 ,일정을 알아내 미래에 대한 일정이 있다면 대화가 끝났을 때 Json 형식으로 정리해줘 답변은 계속 반말로 해줘 너가 정리한다고 했는데 일기는 일기: 이렇게 나타내고 육하원칙은 육하원칙: 이렇게 나타내고 미래일정은 있다면 미래일정: 이렇게 나타내줘 꼭 이 양식을 지켜",
            name=user_info['nickname'] + "의gpt",
            # tools,
            model = "gpt-4-turbo",

        )
        search_assistant = GPTclient.beta.assistants.create( # GPT 검색용 어시스턴트 생성
            instructions="", #json 파일 안에서 만 검색
            name = user_info['nickname'] + "검색 GPT",
            #tools= file_upload,
            model = "gpt-4-turbo",

        )
        print(my_assistant)
        # MongoDB에 사용자 정보 추가
        user_data = {
            'userId': user_info['userId'],
            'nickname': user_info['nickname'],
            'profileImage': user_info['profileImage'],
            'GptID': my_assistant.id,
            'SearchGptID': search_assistant.id,
            'weight': 0
        }
        result = ID_collection.insert_one(user_data)
        print('Inserted user info with ID:', result.inserted_id)
        return jsonify({'message': 'User info received and added to MongoDB successfully'})

@userinfo_api.route('/userinfo/<string:userId>')
class UserInfoAPI(Resource):
    @userinfo_api.response(200, '해당 유저 정보')
    @userinfo_api.response(400, '해당 유저 없음')
    def get(self, userId: str):

        # MongoDB에 아이디 여부 확인
        existing_user = ID_collection.find_one({'userId': userId})

        if existing_user is not None:
            response = {
                'userId': existing_user['userId'],
                'nickname': existing_user['nickname'],  # 예시로 'name' 필드를 가져온 것입니다. 실제 필드 이름에 맞게 수정하세요.
                'profileImage': existing_user['profileImage'],
                'GPTID': existing_user['GptID'],
                'searchGptID': existing_user['SearchGptID'],
                'weight': existing_user['weight']
                # 다른 필요한 정보들도 가져오세요
            }

            return response, 200
        else:
            response = {'message': '해당 유저가 없음'}
            return response, 400

@swagger_api.route('/')
class Test(Resource):
    def get(self):
    	return 'Hello World!'

@swagger_api.route('/test_image<string:userId>')
class test_diary_image(Resource):
    def get(self, userId: str):
        # MongoDB에 아이디 여부 확인
        db = client.SMU_Capston  # 데이터베이스 이름
        Diary_collection = db.diary  # ID 컬렉션.
        existing_user = Diary_collection.find_one({'userId': userId})
        if existing_user is not None:
            response = {
                'image': existing_user['image']
            }
            return response, 200



# @AI_speech_model_api.route('/model', methods=['POST']) #음성 모델 api
# class AI_speech_model_api(Resource):
#     def post(self):
#         file = request.files['fileTest']
#         if file:
#             # 파일 저장 경로
#             upload_folder = 'uploads'
#             # 없으면 생성
#             os.makedirs(upload_folder, exist_ok=True)
#
#             # 파일 저장
#             file_path = os.path.join(upload_folder, file.filename)
#             file.save(file_path)
#
#             #모델 돌리기
#             predicted_emotion = prediction(file_path)
#
#             if predicted_emotion is not None:
#                 return f"감정 상태 : {predicted_emotion}", 200
#             else:
#                 return "감정이 없음", 400
#         else:
#             return "파일 없음", 400

###############AI 모델 합친 코드 #######################
@Send_Message_Dairy_api.route('/model', methods=['POST'])
class Send_Message_Dairy_api(Resource):
    @api.expect(file_upload)
    @api.response(200, '성공',send_message_response)
    def post(self):
        file = request.files['fileTest']
        text = request.form['content']
        threadid = request.form['threadid']
        userid = request.form['userid']
        weight = request.form['weight']

        if file:
            # 파일 저장 경로
            upload_folder = 'uploads'
            # 없으면 생성
            os.makedirs(upload_folder, exist_ok=True)

            # 파일 저장
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)

            #모델 돌리기
            predicted_emotion = prediction(file_path, text, weight)
            predicted_text_emotion = load_and_predict(text)

            #kobert가 돌아가게
            #여기서 문장(텍스트감정, 음성감정) -> gpt 보내줘야함.
            GPTtoText = text + f"({predicted_text_emotion},{predicted_emotion})"
            print("사용자의 대화: ", text)
            print("텍스트 감정: ",predicted_text_emotion,", 음성 감정: ", predicted_emotion)
            if predicted_emotion is not None:
                return gpt.sendGPT(userid,threadid,GPTtoText), 200
            else:
                return "감정이 없음", 400
        else:
            return "파일 없음", 400
@Search_gpt_api.route('/searchgpt', methods=['POST'])
class Search_Message_GPT_api(Resource):
    @api.expect(search_message_model, validate=True)
    @api.response(200,'성공',search_gpt_response)
    def post(self):
        data = request.get_json()
        userId = data['userId']
        threadid = data['threadId']
        text = data['text']

        if userId is not None and threadid is not None and text is not None:
            response = search.searchGPT(userId, threadid,text)
            return response, 200
        else:
            response = {
                "message" : "인자값 오류"
            }
            return response, 400



# @AI_text_model_api.route('/kobert', methods=['POST'])
# class AI_text_model_api(Resource):
#     def post(self):
#         text = request.form['text']
#
#         if text:
#             emotion = load_and_predict(text)
#             return f'Emotion: {emotion}', 200
#         else:
#             return '입력x', 400
@Create_Chatroom_api.route('/chatroom', methods=['POST'])
class CreateChatroom(Resource):
    @Create_Chatroom_api.expect(chat_thread, validate=True)
    @Create_Chatroom_api.response(200, '채팅방 id 생성', chatroom_response_model)
    @Create_Chatroom_api.response(400, '해당 유저 없음', user_not_found_model)
    def post(self):
        data = request.get_json()  # JSON 데이터 가져오기
        userId = data.get('userId')  # userId 추출

        # MongoDB에 아이디 여부 확인
        existing_user = ID_collection.find_one({'userId': userId})

        if existing_user is not None:
            chat_thread = GPTclient.beta.threads.create().id# 채팅방 아이디 생성
            chat_thread_tmp = GPTclient.beta.threads.create().id #채팅방 아이디 생성 (임시)

            tmp_response = gpt.sendGPT(userId, chat_thread_tmp,"안녕(중립,중립)")
            data = tmp_response
            print("임시 챗봇 스레드: ",chat_thread_tmp)
            message = data['message']
            emotion = data['emotion']
            response = {
                'chat_thread': chat_thread,
                'message': message,
                'emotion': emotion
            }
            return response, 200
        else:
            response = {'message' : '해당 유저가 없음'}
            return response, 400
@Create_Diary_api.route('/diary', methods=['POST'])
class CreateDiary(Resource):
    @Create_Diary_api.expect(diary_info, validate=True)
    @Create_Diary_api.response(200, '다이어리 생성', create_diary_response)
    @Create_Diary_api.response(400, '다이어리 생성 실패')
    def post(self):
        data = request.get_json()
        userId = data.get('userId')
        threadId = data.get('threadId')
        count = data.get('count')

        existing_user = ID_collection.find_one({'userId': userId})

        if existing_user is not None:
            gpt.create_diary(threadId, userId, count)
            response = {'message' : '일기 생성 완료'}
            return response, 200
        else:
            response = {'message' : '일기 생성 실패'}
            return response, 400
@Search_Diary_api.route('/searchdiary', methods=['POST'])
class SearchDiary(Resource):
    @api.expect(diary_model, validate=True)
    @Search_Diary_api.response(200,"userId(필수)만 주면 해당 Id의 전체 일기 -- month랑 같이 주면 해당달 -- date랑 같이 주면 해당날짜", search_diary_response)
    def post(self):
        data = request.get_json()
        userid = data.get("userId")
        date = data.get('date')  # 'date' 쿼리 매개변수, 없을 경우 기본값은 None
        month = data.get('month')  # 'month' 쿼리 매개변수, 없을 경우 기본값은 None
        limit = data.get('limit') # 0이 기본값 0이 아니면 최근 일기
        if date == 'None':
            date = None
        if month == 'None':
            month = None
        if limit == 'None':
            limit = None
        print(date,month,userid,limit)
        #month = int(month) if month is not None else None  # 'month'를 int로 변환, None이면 None 유지
        limit = int(limit) if limit is not None else None
        response = diary.searchDiary(userid, date, month, limit)
        return response

@Count_Month_Emotion_api.route('/countmonthemotion', methods=['POST'])
class CountMonthemotion(Resource):
    @api.expect(month_count_model, validate=True)
    @Count_Month_Emotion_api.response(200, "성공",month_count_response)
    def post(self):
        data = request.get_json()
        userid = data.get("userId")
        month = data.get("month")
        if userid is not None and month is not None:
            #month = int(month) if month is not None else None
            response = emotion_count.emotion_count_month(userid, month)
            print("한달 내 (텍스트, 음성, 최종감정) 갯수 ",response)
            return response
        else:
            response = "인자값 오류"
            return response
@month_feedback_api.route('/monthfeedback', methods=['POST'])
class MonthFeedbackAPI(Resource):
    @api.expect(month_feedback_model, validate=True)
    @month_feedback_api.response(200, "성공", month_feedback_response)
    def post(self):
        data = request.get_json()
        userid = data.get("userId")
        #month_max_emotion = data.get("month_max_emotion")
        emotion_list = data.get("emotion_list")
        if userid is not None and emotion_list is not None:
            response = feedback.feedbackGPT(userid, emotion_list)#month_max_emotion
            return response
        else:
            response = {
                "message" : "인자값 오류"
            }
            return response


@get_future_api.route('/getfuture/<string:userId>/<string:month>', methods=['GET'])
class GetFuture(Resource):
    @api.response(200, '미래 일정 불러오기 완료', get_future_response)
    def get(self, userId: str, month: str):
        future_collection = db.future
        existing_user = future_collection.find_one({'userId': userId})
        if not existing_user:
            return {'message': '해당 유저가 없음'}, 404

        # 입력받은 year_month를 연도와 월로 분리합니다.
        year, month = map(int, month.split('-'))

        # 입력된 월의 첫 날과 마지막 날을 계산합니다.
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)

        cursor = future_collection.find({
            'userId': userId,
            'date': {'$gte': start_of_month, '$lt': end_of_month}
        })
        print("userID date", cursor)
        results = []
        for result in cursor:
            response = {
                'content': result['content'],
                # datetime 객체를 "YYYY-MM-DD" 형식의 문자열로 변환
                'date': result['date'].strftime('%Y-%m-%d')
            }
            results.append(response)
            print("results",results)

        if results:
            return results, 200
        else:
            return {'message': '해당 유저의 미래 일정이 없음'}, 404

@get_future_api.route('/getfuture/<string:userId>', methods=['GET'])
class GetFutureAll(Resource):
    @api.response(200, '미래 일정 불러오기 완료', get_future_response)
    def get(self, userId: str):
        future_collection = db.future
        existing_user = future_collection.find_one({'userId': userId})
        if not existing_user:
            return {'message': '해당 유저가 없음'}, 404

        cursor = future_collection.find({
            'userId': userId,
        })
        print("userID date", cursor)
        results = []
        for result in cursor:
            response = {
                'content': result['content'],
                # datetime 객체를 "YYYY-MM-DD" 형식의 문자열로 변환
                'date': result['date'].strftime('%Y-%m-%d')
            }
            results.append(response)
            print("results",results)

        if results:
            return results, 200
        else:
            return {'message': '해당 유저의 미래 일정이 없음'}, 404

@Set_weight_api.route('/weight', methods=['POST'])
class Set_weight_api(Resource):
    @api.expect(user_weight_file_upload)
    @api.response(200, '성공',Set_weight_response)
    def post(self):
        file1 = request.files['file1']
        file2 = request.files['file2']
        file3 = request.files['file3']
        file4 = request.files['file4']
        file5 = request.files['file5']
        userid = request.form['userid']
        weight = 0
        cnt = 0
        for file in [file1, file2, file3, file4, file5]:
            if file:
                # 파일 저장 경로
                upload_folder = 'uploads'
                # 없으면 생성
                os.makedirs(upload_folder, exist_ok=True)

                # 파일 저장
                file_path = os.path.join(upload_folder, file.filename)
                file.save(file_path)

                #모델 돌리기
                predicted_emotion = pre_prediction(file_path)
                if predicted_emotion != 0.0:
                    cnt += 1
                    weight = weight + predicted_emotion

            else:
                return "파일 없음", 400
        if cnt > 0 :
            final_weight = weight/cnt
        else:
            final_weight = 0

        #mongoDB 업데이트
        result = ID_collection.update_one(
            {'userId': userid},
            {'$set': {'weight': final_weight}}
        )

        if result.matched_count > 0:
            return {"message": "사용자 맞춤 가중치 설정 완료"}, 200
        else:
            return {"message": "사용자를 찾을 수 없음"}, 404

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True) #모든 ip 에서 접속 가능하도록 0.0.0.0