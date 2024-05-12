import app

def emotion_count_month(userid, month):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userid})
    print("검색 시작")
    if cursor is not None:
        print("검색 성공")
        TextEM = []
        SpeechEM = []

        neutral = 0
        angry = 0
        sad = 0
        happy = 0

        embrassed = 0
        hurt = 0
        anxiety = 0
        for result in cursor:
            print("for문 시작")
            diary_date = result['Date']
            diary_month = int(diary_date.split('-')[1])  # 다이어리의 월을 추출합니다.
            if diary_month == month:
                TextEM.extend(result['textEmotion'])
                SpeechEM.extend(result['speechEmotion'])
                print(TextEM, SpeechEM)
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
        print(neutral,sad,angry,happy,anxiety,embrassed,hurt)

    else:
        return "유저 정보를 찾을 수 없습니다.", 400
    return TextEM, SpeechEM