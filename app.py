import os
import torch
from flask import Flask, request, url_for, session, redirect, jsonify
from flask_restx import Api, Resource,fields, reqparse #swagger 명세서
from pymongo import collection

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime

from emotion_model import prediction
from kobert import load_and_predict

import apikey
from openai import OpenAI
#MongoDB 연결
uri = "mongodb+srv://qqqaaaccc:0MgyTiCM067afKHj@jaemin.jyhcm0g.mongodb.net/?retryWrites=true&w=majority&appName=Jaemin"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client.SMU_Capston  # 데이터베이스 이름
ID_collection = db.users  # ID 컬렉션.


app = Flask(__name__)

######Swagger######
#Swagger 명세서 만들기 경로 설정
api = Api(app, version='1.0', title='API 문서', description='Swagger 문서', doc="/a")
swagger_api = api.namespace('test', description='조회 API')
login_api = api.namespace('login', description='카카오 로그인 / 회원가입 API' )
AI_speech_model_api = api.namespace('AI_speech_model', description='AI 음성 모델 호출')
AI_text_model_api = api.namespace('AI_text_model', description='AI 텍스트 모델 호출')

#사용자 정보 모델 정의
user_model = api.model('User', {
    'userId': fields.String(required=True, description='User ID'),
    'nickname': fields.String(required=True, description='User Nickname')
})
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
            return jsonify({'message': 'User already exists in MongoDB'}), 400  # 이미 존재하는 사용자인 경우 클라이언트에게 에러 응답을 전송
        #유저별 GPT
        client = OpenAI(
            api_key=apikey
        )

        my_assistant = client.beta.assistants.create( # GPT 어시스턴트 생성
            instructions="",
            name=user_info['nickname'] + "의gpt",
            # tools,
            model = "gpt-3.5-turbo",

        )
        print(my_assistant)
        # MongoDB에 사용자 정보 추가
        user_data = {
            'userId': user_info['userId'],
            'nickname': user_info['nickname'],
            'GptID': my_assistant.id
        }
        result = ID_collection.insert_one(user_data)
        print('Inserted user info with ID:', result.inserted_id)

        return jsonify({'message': 'User info received and added to MongoDB successfully'})

@swagger_api.route('/')
class Test(Resource):
    def get(self):
    	return 'Hello World!'

@swagger_api.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return "hello world"

# 계산기 API###############################################################
# @app.route('/add', methods=['POST'])
# def add():
#   left = request.form['left']
#   rite = request.form['rite']
#   return str(int(left) + int(rite))
#
# @app.route('/multiply', methods=['POST'])
# def multiply():
#   left = request.form['left']
#   rite = request.form['rite']
#   return str(int(left) * int(rite))
#########################################################################

@AI_speech_model_api.route('/model', methods=['POST']) #음성 모델 api
class AI_speech_model_api(Resource):
    def post(self):
        file = request.files['fileTest']
        if file:
            # 파일 저장 경로
            upload_folder = 'uploads'
            # 없으면 생성
            os.makedirs(upload_folder, exist_ok=True)

            # 파일 저장
            file_path = os.path.join(upload_folder, file.filename)
            file.save(file_path)

            #모델 돌리기
            predicted_emotion = prediction(file_path)

            if predicted_emotion is not None:
                return f"감정 상태 : {predicted_emotion}", 200
            else:
                return "감정이 없음", 400
        else:
            return "파일 없음", 400
@AI_text_model_api.route('/kobert', methods=['POST'])
class AI_text_model_api(Resource):
    def post(self):
        text = request.form['text']

        if text:
            emotion = load_and_predict(text)
            return f'Emotion: {emotion}', 200
        else:
            return '입력x', 400

# @app.route('/cal', methods=['POST'])
# def calculate_pitch_analysis(file_path):
#     try:
#         # 음성 파일 로드
#         audio_sample, sampling_rate = librosa.core.load(file_path, sr=None)
#
#         # STFT 계산, window 수정해 줘야함
#         S = np.abs(librosa.stft(audio_sample, n_fft=1024, hop_length=512, win_length=1024, window='hann'))
#
#         # 피치 추출
#         pitches, magnitudes = librosa.piptrack(S=S, sr=sampling_rate)
#
#         # 피치 평균 계산
#         shape = np.shape(pitches)
#         nb_windows = shape[1]
#
#         sum_of_pitches = 0.0
#         count_valid_pitches = 0
#
#         for i in range(nb_windows):
#             index = magnitudes[:, i].argmax()
#             pitch = pitches[index, i]
#             if pitch > 0:
#                 sum_of_pitches += pitch
#                 count_valid_pitches += 1
#
#         # 유효한 피치 값들의 평균 계산
#         if count_valid_pitches > 0:
#             average_pitch = sum_of_pitches / count_valid_pitches
#             return average_pitch
#         else:
#             return None
#
#     except Exception as e:
#         print(f"Error processing file: {e}")
#         return None
#
#
# @app.route('/tt', methods=['POST'])
# def apiTest():
#     # 멀티파트 요청에서 파일 데이터 추출
#     file = request.files['fileTest']
#     if file:
#         # 파일 저장 경로
#         upload_folder = 'uploads'
#         # 없으면 생성
#         os.makedirs(upload_folder, exist_ok=True)
#
#         # 파일 저장
#         file_path = os.path.join(upload_folder, file.filename)
#         file.save(file_path)
#
#         # 음성 파일 분석 및 평균 피치 계산
#         average_pitch = calculate_pitch_analysis(file_path)
#
#         if average_pitch is not None:
#             return f"피치 평균: {average_pitch}", 200  # 평균 피치 반환 (200 OK)
#         else:
#             return "피치가 없음", 400
#     else:
#         return "파일 없음", 400


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True) #모든 ip 에서 접속 가능하도록 0.0.0.0