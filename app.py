import os

from flask import Flask, request, url_for, session, redirect, jsonify


from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import datetime

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
db = client.my_database

collection = db.my_collection
document1 = {"name": "홍길동",
            "bio": "한국인입니다.",
            "tags": ["#몽고디비", "#파이썬", "#플라스크"],
            "date": datetime.datetime.utcnow()}

document2 = {"name": "영희",
             "bio": "한국인입니다.",
             "tags": ["#MongoDB", "#Python", "#Flask"],
             "date": datetime.datetime.utcnow()}
L = [document1, document2]
collection.insert_many(L)


app = Flask(__name__)
###############

@app.route('/receive_user_info', methods=['POST'])
def receive_user_info():
    user_info = request.get_json()
    # 여기서 받은 사용자 정보를 처리하는 코드 작성
    print('Received user info:', user_info)
    return jsonify({'message': 'User info received successfully'})

@app.route("/hello", methods=['GET'])
def hello():
  return "hello world"

@app.route('/add', methods=['POST'])
def add():
  left = request.form['left']
  rite = request.form['rite']
  return str(int(left) + int(rite))

@app.route('/multiply', methods=['POST'])
def multiply():
  left = request.form['left']
  rite = request.form['rite']
  return str(int(left) * int(rite))

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
  app.run(host='0.0.0.0', port=5000, debug=True)