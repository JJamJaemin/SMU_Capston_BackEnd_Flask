import app

def user_chatbot_feedback(userid, content):
    db = app.client.SMU_Capston  # 데이터베이스 이름
    User_collection = db.users  # ID 컬렉션.
    cursor = User_collection.find({'userId': userid})

    if cursor is not None:
        cursor = User_collection.find_one({
            'userId': userid
        })

        GptID = cursor['GptID']
        existAssi = cursor['GPTAssi']

        print("기존 어시 내용")
        print(existAssi)

        newAssi = existAssi + '\n' + content
        print("요청 사항 추가 내용")
        print(newAssi)

        new_Assistant = app.GPTclient.beta.assistants.update(
            assistant_id=GptID,
            instructions=newAssi,
        )

        # mongoDB 업데이트
        result = User_collection.update_one(
            {'userId': userid},
            {'$set': {'GPTAssi': newAssi}}
        )

        response = {'message': '요청사항이 반영되었습니다!'}

        return response, 200
    else:
        return "유저 정보를 찾을 수 없습니다.", 400