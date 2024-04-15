import keras
import os
import numpy as np
import librosa
import pickle

# 현재 스크립트 파일의 절대 경로를 가져옵니다.
script_path = os.path.abspath(__file__)
# 스크립트 파일이 있는 디렉토리의 경로를 가져옵니다.
script_directory = os.path.dirname(script_path)

# 파일의 상대 경로를 지정합니다.
model_route = 'src/best_model1_weights.h5'
cnn_route = 'src/CNN_model.json'
encoder_route = 'src/encoder2.pickle'
scaler_route = 'src/scaler2.pickle'

# 파일의 절대 경로를 구성합니다.
model_path = os.path.join(script_directory, model_route)
cnn_js_path = os.path.join(script_directory, cnn_route)
encoder_path = os.path.join(script_directory, encoder_route)
scaler_path = os.path.join(script_directory, scaler_route)

json_file = open(cnn_js_path, 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model = keras.models.model_from_json(loaded_model_json)
loaded_model.load_weights(model_path)

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
    print(res.shape)

    #shape가 안맞는 음성 파일 강제로 맞춰주기
    if len(res) < 2376:
        res = np.pad(res, (0, 2376 - len(res)), mode='constant')
    elif len(res) > 2376:
        res = res[:2376]

    result = np.array(res)
    result = np.reshape(result, newshape=(1, 2376))
    i_result = scaler2.transform(result)
    final_result = np.expand_dims(i_result, axis=2)

    return final_result

def prediction(path1):
    res=get_predict_feat(path1)
    predictions=loaded_model.predict(res)
    y_pred = encoder2.inverse_transform(predictions)

    return y_pred[0][0]