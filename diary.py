from datetime import datetime, timedelta

import app


def searchDiary(userid, date, month, limit):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.

    existing_user = Diary_collection.find_one({'userId': userid})
    if existing_user:
        if date is None and month is not None and limit is None: #해당 달
            print("해당 달에 대한 검색 시작")
            response = diary_month(userid, month)
            print("검색 완료")

            return response
        elif date is None and month is None and limit is None: #사용자의 전체 일기
            print("사용자 일기 전체 검색 시작")
            response = diary_all(userid)
            print("검색 완료")

            return response
        elif date is not None and month is None and limit is None: #해당 날짜 일기
            print("해당 날짜 일기 검색 시작")
            response = diary_date(userid,date)
            print("검색 완료")
            return response

        elif date is None and month is None and limit is not None: # 최근 일기
            print("최근 일기 검색 시작")
            response = diary_current(userid,limit)
            print("검색 완료")
            return response

        return {'사용자의 일기 존재 확인'}
    else:
        return {'사용자의 일기가 존재 하지 않습니다.'}


def diary_date(userId,date):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    input_date = datetime.strptime(date, '%Y-%m-%d')
    # 날짜 범위를 만들어 해당 일자의 시작과 끝을 지정합니다.
    start_of_day = datetime(input_date.year, input_date.month, input_date.day, 0, 0, 0)
    end_of_day = datetime(input_date.year, input_date.month, input_date.day, 23, 59, 59)

    # MongoDB 쿼리를 수정하여 일자 범위 내의 문서를 찾습니다.
    cursor = Diary_collection.find({
        'userId': userId,
        'date': {
            '$gte': start_of_day,
            '$lte': end_of_day
        }
    })
    #cursor = Diary_collection.find({'userId': userId, 'date' : date})
    if cursor is not None:
        diaries = []

        for result in cursor:
            response = {
                'userId': result['userId'],
                'date': str(result['date']),
                'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'absEmotion': result['absEmotion'],
                'chatCount': result['chatCount'],
                'feedback': result['feedback'],
                'changeEmotion': result['changeEmotion'],  # [배열형태 감정 2개]
                'small_emotion': result['smallEmotion'],  # 소 감정[[]]
                'AIChating': result['AIChating'],  # 공감 해준 메시지 찾은것
                'case': result['case'],  # case1 = 1 case2 = 2
                'changeComment': result['changeComment'], # 감정 변화에 대한 코멘트들을 준 것
            }
            diaries.append(response)

        if diaries:
            return diaries, 200
        else:
            return "해당하는 날짜의 일기가 없습니다.", 404
    else:
        return "유저 정보를 찾을 수 없습니다.", 400

def diary_all(userId):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userId})
    if cursor is not None:
        diaries = []

        for result in cursor:
            response = {
                'userId': result['userId'],
                'date': str(result['date']),
                'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'absEmotion': result['absEmotion'],
                'chatCount': result['chatCount'],
                'feedback': result['feedback'],
                'changeEmotion': result['changeEmotion'],  # [배열형태 감정 2개]
                'small_emotion': result['smallEmotion'],  # 소 감정[[]]
                'AIChating': result['AIChating'],  # 공감 해준 메시지 찾은것
                'case': result['case'],  # case1 = 1 case2 = 2
                'changeComment': result['changeComment'], # 감정 변화에 대한 코멘트들을 준 것
            }
            diaries.append(response)
        if diaries:
             return diaries, 200
        else:
            return "해당 유저에 맞는 다이어리가 없습니다", 404
    else:
        return "유저 정보를 찾을 수 없습니다.", 400

def diary_month(userId, month):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    # 입력받은 year_month를 연도와 월로 분리합니다.
    year, month = map(int, month.split('-'))

    # 입력된 월의 첫 날과 마지막 날을 계산합니다.
    start_of_month = datetime(year, month, 1)
    if month == 12:
        end_of_month = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end_of_month = datetime(year, month + 1, 1) - timedelta(seconds=1)

    # 해당 월에 해당하는 모든 일기를 검색합니다.
    cursor = Diary_collection.find({
        'userId': userId,
        'date': {
            '$gte': start_of_month,
            '$lt': end_of_month
        }
    })

    if cursor is not None:
        diaries = []

        for result in cursor:
            response = {
                'userId': result['userId'],
                'date': str(result['date']),
                'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'absEmotion': result['absEmotion'],
                'chatCount': result['chatCount'],
                'feedback': result['feedback'],
                'changeEmotion': result['changeEmotion'],  # [배열형태 감정 2개]
                'small_emotion': result['smallEmotion'], #소 감정[[]]
                'AIChating': result['AIChating'],  # 공감 해준 메시지 찾은것
                'case': result['case'],  # case1 = 1 case2 = 2
                'changeComment': result['changeComment'],  # 감정 변화에 대한 코멘트들을 준 것
            }
            diaries.append(response)
        if diaries:
            return diaries, 200
        else:
            return "해당 월에 다이어리가 없습니다.", 404
    else:
        return "유저 정보를 찾을 수 없습니다.", 400

def diary_current(userId,limit):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userId}).limit(limit)
    if cursor is not None:
        diaries = []

        for result in cursor:
            response = {
                'userId': result['userId'],
                'date': str(result['date']),
                'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'absEmotion': result['absEmotion'],
                'chatCount': result['chatCount'],
                'feedback': result['feedback'],
                'changeEmotion': result['changeEmotion'],  # [배열형태 감정 2개]
                'small_emotion': result['smallEmotion'],  # 소 감정[[]]
                'AIChating': result['AIChating'],  # 공감 해준 메시지 찾은것
                'case': result['case'],  # case1 = 1 case2 = 2
                'changeComment': result['changeComment'],  # 감정 변화에 대한 코멘트들을 준 것
            }
            diaries.append(response)
        if diaries:
             return diaries, 200
        else:
            return "해당 유저에 맞는 다이어리가 없습니다", 404
    else:
        return "유저 정보를 찾을 수 없습니다.", 400

