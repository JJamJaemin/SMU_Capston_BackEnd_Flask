from datetime import datetime, timedelta

import app

def emotion_count_month(userid, month):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userid})
    text_abs_count = []
    speech_abs_count = []
    abs_abs_count = []
    print("검색 시작")
    if cursor is not None:
        print("검색 성공")
        TextEM = []
        SpeechEM = []
        absoluteEM = []

        neutral = 0
        angry = 0
        sad = 0
        happy = 0
        embrassed = 0
        hurt = 0
        anxiety = 0
        # 입력받은 year_month를 연도와 월로 분리합니다.
        year, month = map(int, month.split('-'))

        # 입력된 월의 첫 날과 마지막 날을 계산합니다.
        start_of_month = datetime(year, month, 1)
        if month == 12:
            end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)

        cursor = Diary_collection.find({
            'userId': userid,
            'date': {
                '$gte': start_of_month,
                '$lt': end_of_month
            }
        })
        for result in cursor:
            print("for문 시작")
            diary_date = str(result['date'])
            diary_str = datetime.strptime(diary_date, "%Y-%m-%d %H:%M:%S.%f")
            diary_month = diary_str.month
            if diary_month == month:
                TextEM.extend(result['textEmotion'])
                SpeechEM.extend(result['speechEmotion'])
                print("감정배열, 음성배열",TextEM, SpeechEM)
        # for result in cursor:
        #     print("for문 시작")
        #     diary_date = str(result['date'])
        #     diary_str = datetime.strptime(diary_date, "%Y-%m-%d %H:%M:%S.%f")
        #     diary_month = diary_str.month
        #     if diary_month == month:
        #         TextEM.extend(result['textEmotion'])
        #         SpeechEM.extend(result['speechEmotion'])
        #         print("감정배열, 음성배열",TextEM, SpeechEM)
        for i in TextEM:
            if i == '중립':
                neutral += 1
            elif i == '슬픔':
                sad += 1
            elif i == '분노':
                angry += 1
            elif i == '행복':
                happy += 1
            elif i == '불안':
                anxiety += 1
            elif i == '당황':
                embrassed += 1
            elif i == '상처':
                hurt += 1
        text_abs_count.append(neutral)
        text_abs_count.append(sad)
        text_abs_count.append(angry)
        text_abs_count.append(happy)
        text_abs_count.append(anxiety)
        text_abs_count.append(embrassed)
        text_abs_count.append(hurt)
        neutral = 0
        angry = 0
        sad = 0
        happy = 0
        embrassed = 0
        hurt = 0
        anxiety = 0
        for i in SpeechEM:
            if i == '중립':
                neutral += 1
            elif i == '슬픔':
                sad += 1
            elif i == '분노':
                angry += 1
            elif i == '행복':
                happy += 1
            elif i == '불안':
                anxiety += 1
            elif i == '당황':
                embrassed += 1
            elif i == '상처':
                hurt += 1
        speech_abs_count.append(neutral)
        speech_abs_count.append(sad)
        speech_abs_count.append(angry)
        speech_abs_count.append(happy)
        speech_abs_count.append(anxiety)
        speech_abs_count.append(embrassed)
        speech_abs_count.append(hurt)

        count = 0
        for i in TextEM:
            if i == SpeechEM[count]:
                absoluteEM.append(i)
            elif i == '중립' and SpeechEM[count] != '중립':
                absoluteEM.append(SpeechEM[count])
            elif i == '불안' :
                absoluteEM.append('불안')
            elif i == '당황':
                absoluteEM.append('당황')
            elif i == '상처':
                absoluteEM.append('상처')
            elif i != '중립' and SpeechEM[count] == '중립':
                absoluteEM.append(i)
            else:
                absoluteEM.append('중립')
            count += 1
        print("최종감정",absoluteEM)

        neutral = 0
        angry = 0
        sad = 0
        happy = 0
        embrassed = 0
        hurt = 0
        anxiety = 0
        for i in absoluteEM:
            if i == '중립':
                neutral += 1
            elif i == '슬픔':
                sad += 1
            elif i == '분노':
                angry += 1
            elif i == '행복':
                happy += 1
            elif i == '불안':
                anxiety += 1
            elif i == '당황':
                embrassed += 1
            elif i == '상처':
                hurt += 1
        abs_abs_count.append(neutral)
        abs_abs_count.append(sad)
        abs_abs_count.append(angry)
        abs_abs_count.append(happy)
        abs_abs_count.append(anxiety)
        abs_abs_count.append(embrassed)
        abs_abs_count.append(hurt)

    else:
        return "유저 정보를 찾을 수 없습니다.", 400
    print("텍스트 감정 갯수 , 음성 감정 갯수 , 최종감정 감정 갯수",text_abs_count,speech_abs_count,abs_abs_count)
    a = 0
    for i in range(0,len(abs_abs_count)):
        if abs_abs_count[i] == 0:
            a += 1
    if a == 7:
        return "해당 날에 대한 감정 정보가 없습니다."
    month_max_emotion = []
    # 감정에 해당하는 배열
    emotions = ['netural', 'sad', 'angry', 'happy', 'anxiety', 'embrassed', 'hurt']

    total = list(zip(emotions, abs_abs_count))
    sort_total = sorted(total, key=lambda x: x[1], reverse=True)

    max = sort_total[0][1]
    for i in range(0, len(sort_total)):
        if sort_total[i][1] == max:
            month_max_emotion.append(sort_total[i][0])


    response = {
        "textCount": text_abs_count,
        "speechCount": speech_abs_count,
        "absTextCount": abs_abs_count,
        "month_max_emotion": month_max_emotion
    }
    return response

def diary_emotion_count(userid):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userid})