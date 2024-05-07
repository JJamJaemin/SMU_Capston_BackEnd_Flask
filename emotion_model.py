import keras
import os
import numpy as np
import librosa
import pickle

# 현재 스크립트 파일의 절대 경로를 가져옵니다.
script_path = os.path.abspath(__file__)
# 스크립트 파일이 있는 디렉토리의 경로를 가져옵니다.
script_directory = os.path.dirname(script_path)
#1 -> 한국어 합성 데이터 2 -> 남성만
# 파일의 상대 경로를 지정합니다.
model_route = 'src/clstm/we_3/best_model3_weights.h5'
cnn_route = 'src/clstm/we_3/CNN_model3.json'
encoder_route = 'src/clstm/we_3/encoder3.pickle'
scaler_route = 'src/clstm/we_3/scaler3.pickle'
audio_route = 'uploads/s_hh1.wav'

# 파일의 절대 경로를 구성합니다.
model_path = os.path.join(script_directory, model_route)
cnn_js_path = os.path.join(script_directory, cnn_route)
encoder_path = os.path.join(script_directory, encoder_route)
scaler_path = os.path.join(script_directory, scaler_route)
audio_route = os.path.join(script_directory, audio_route)

json_file = open(cnn_js_path, 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model = keras.models.model_from_json(loaded_model_json)
loaded_model.load_weights(model_path)

#loaded_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

with open(scaler_path, 'rb') as f:
    scaler2 = pickle.load(f)

with open(encoder_path, 'rb') as f:
    encoder2 = pickle.load(f)

#y=data로 바꿔야 인자값이 들어가짐
def zcr(data, frame_length, hop_length):
    zcr = librosa.feature.zero_crossing_rate(y=data, frame_length=frame_length, hop_length=hop_length)
    return np.squeeze(zcr)

def rmse(data, frame_length=2048, hop_length=512):
    rmse = librosa.feature.rms(y=data, frame_length=frame_length, hop_length=hop_length)
    return np.squeeze(rmse)

def mfcc(data, sr, frame_length=2048, hop_length=512, flatten: bool = True):
    mfcc = librosa.feature.mfcc(y=data, sr=sr)
    return np.squeeze(mfcc.T) if not flatten else np.ravel(mfcc.T)

# def extract_features(data, sr=22050, frame_length=2048, hop_length=512):
#     result = np.array([])
#
#     result = np.hstack((result,
#                         zcr(data, frame_length, hop_length),
#                         rmse(data, frame_length, hop_length),
#                         mfcc(data, sr, frame_length, hop_length)
#                         ))
#     return result
#
# def get_predict_feat(path):
#     d, s_rate = librosa.load(path, duration=2.5, offset=0.6)
#     res = extract_features(d)
#     print(res.shape)
#
#     #shape가 안맞는 음성 파일 강제로 맞춰주기
#     if len(res) < 2376:
#         res = np.pad(res, (0, 2376 - len(res)), mode='constant')
#     elif len(res) > 2376:
#         res = res[:2376]
#
#     result = np.array(res)
#     result = np.reshape(result, newshape=(1, 2376))
#     i_result = scaler2.transform(result)
#     final_result = np.expand_dims(i_result, axis=2)
#
#     return final_result
#
# def prediction(path1):
#     res=get_predict_feat(path1)
#     predictions=loaded_model.predict(res)
#     y_pred = encoder2.inverse_transform(predictions)
#
#     return y_pred[0][0]

#확률 출력

def extract_features(data, sr=22050, frame_length=2048, hop_length=512):
    result = np.array([])

    result = np.hstack((result,
                        zcr(data, frame_length, hop_length),
                        rmse(data, frame_length, hop_length),
                        mfcc(data, sr, frame_length, hop_length)
                        ))
    return result


def get_predict_feat(path):
    d, s_rate = librosa.load(path, duration=2.5, offset=0.6)
    res = extract_features(d)
    #print(res.shape)

    if len(res) < 2376:
        res = np.pad(res, (0, 2376 - len(res)), mode='constant')
    elif len(res) > 2376:
        res = res[:2376]

    result = np.array(res)
    result = np.reshape(result, newshape=(1, 2376))
    i_result = scaler2.transform(result)
    #print(i_result)
    final_result = np.expand_dims(i_result, axis=2)
    #print(final_result)

    return final_result

#emotions1={0:'angry', 1:'anxious', 2:'embarrassed', 3:'happy', 4:'hurt', 5:'neutral', 6:'sad'}
def prediction(path1, content):
    res = get_predict_feat(path1)
    predictions = loaded_model.predict(res)
    #y_pred = encoder2.inverse_transform(predictions)
    #print(predictions)
    #print("######")
    sorted_indices = np.arange(predictions[0].size)
    #print(sorted_indices)

    #print(encoder2.categories_)

    pro_list = [] #감정 순서 neutral happy sad angry
    for idx in sorted_indices:
        label = encoder2.categories_[0][idx]
        probability = predictions[0][idx]
        pro_list.append([label, probability])
        #print(pro_list)
        #print(f"{label}: {probability:.3f}")

    #print(pro_list)

    positive_words = [
        "행복", "기쁘다", "기뻐","웃다", "즐겁다", "흐뭇하다", "만족하다", "설레다", "감사하다", "뿌듯하다",
        "행복감", "미소", "만족", "쾌감", "사랑하다", "행운", "호감", "평화롭다", "안도하다", "신나다",
        "고맙다", "즐거움", "흥분하다", "감동하다", "행복해하다", "아늑하다", "편안", "희열",
        "더할 나위 없다", "들뜨다", "영광", "좋아"
    ]

    test_sentence = content
    words = test_sentence.split()

    for i in words:
        if any(positive_word in i for positive_word in positive_words):
            # emotion, probability = pro_list[1]
            # pro_list[1] = [emotion, probability + 0.1]
            pro_list[1][1] += 0.1

            #print(i)
        else:
            print("기본")

    #print(pro_list)

    if abs(pro_list[2][1] > pro_list[0][1] and pro_list[2][1] > pro_list[1][1] and pro_list[3][1] > pro_list[0][1] and pro_list[3][1] > pro_list[1][1]):
        pro_list[3][1] -= 0.095
        print("가중치 감소")

    #print(pro_list)

    max_emotion = max(pro_list, key=lambda x: x[1])[0]
    #print(max_emotion)
    if max_emotion == "neutral":
        max_emotion = "슬픔"
    elif max_emotion == "sad":
        max_emotion = "중립"
    elif max_emotion == "angry":
        max_emotion = "분노"
    elif max_emotion == "happy":
        max_emotion = "행복"
    return max_emotion


# test = prediction(audio_route)
#
# print(test)