from datetime import datetime

import app


def searchDiary(userid, date, month):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.

    existing_user = Diary_collection.find_one({'userId': userid})
    if existing_user:
        if date is None and month is not None: #해당 달
            response = diary_month(userid, month)

            return response
        elif date is None and month is None: #사용자의 전체 일기
            response = diary_all(userid)

            return response
        elif date is not None and month is None: #해당 날짜 일기

            response = diary_date(userid,date)

            return response
        return {'사용자의 일기 존재 확인'}
    else:
        return {'사용자의 일기가 존재 하지 않습니다.'}


def diary_date(userId, Date):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    Diary_collection = db.diary  # ID 컬렉션.
    cursor = Diary_collection.find({'userId': userId, 'Date' : Date})
    if cursor is not None:
        diaries = []

        for result in cursor:
            response = {
                'userId': result['userId'],
                'Date': result['Date'],
                #'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'chatCount': result['chatCount']
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
                'Date': result['Date'],
                #'image': result['image'],
                'content': result['content'],
                'textEmotion': result['textEmotion'],
                'speechEmotion': result['speechEmotion'],
                'chatCount': result['chatCount']
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
    cursor = Diary_collection.find({'userId': userId})
    if cursor is not None:
        diaries = []

        for result in cursor:
            diary_date = result['Date']
            diary_month = int(diary_date.split('-')[1])  # 다이어리의 월을 추출합니다.
            if diary_month == month:
                response = {
                    'userId': result['userId'],
                    'Date': result['Date'],
                    #'image': result['image'],
                    'content': result['content'],
                    'textEmotion': result['textEmotion'],
                    'speechEmotion': result['speechEmotion'],
                    'chatCount': result['chatCount']
                }
                diaries.append(response)
        if diaries:
            return diaries, 200
        else:
            return "해당 월에 다이어리가 없습니다.", 404
    else:
        return "유저 정보를 찾을 수 없습니다.", 400