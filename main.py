from flask import Flask, render_template, redirect, request, jsonify
import pymysql
import os

app = Flask(__name__,static_url_path='')

# 链接数据库
db = pymysql.connect(host="localhost",user="root",password="Hx1551986048",database="api")

# 配置上传的视频文件夹
UPLOAD_FOLDER = 'data'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保上传文件夹存在
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def count_files(path):
    file_count = 0
    for root, dirs, files in os.walk(path):
        file_count += len(files)
    return file_count


@app.route('/')
def index():
    return render_template('QPS.html')
        

@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('username')
    password = request.args.get('password')
    
    cursor = db.cursor()
    sql = "select * from user where username = '%s' and password = '%s'"
    param = (username, password)
    
    try:
        cursor.execute(sql%param)
        result = cursor.fetchone()
        if result == None:
            # 登录失败
            data = {
                'answer': '登录失败'
            }
            return jsonify(data)
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400
    
    # 登录成功
    data = {
        'answer': '登录成功',
        'user_id': result[2] 
    }
    return jsonify(data)


@app.route('/register', methods=['PUT'])
def register():
    data = request.get_json()
    if not data:
        result = {
            'error': 'No Data Provided'
        }
        return jsonify(result)
    username = data.get('username')
    password = data.get('password')

    try:
        cursor = db.cursor()
        sql = "insert into user (username, password) values('%s', '%s')"
        param = (username, password)
        cursor.execute(sql%param)
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400
    
    result = {
        'answer': '注册成功'
    }
    return jsonify(result)


# 发布视频
@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    file = request.files['video']
    user_id = request.form.get('user_id')
    name = request.form.get('name')
    if user_id == None or name == None:
        return jsonify({'error': 'No user_id or name provided'}), 400
    
    file.filename = 'video_' + str(count_files('data') + 1) + '.mp4'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        sql_1 = "insert into video (name, path) values('%s', '%s')"
        param_1 = (name, file_path)

        cursor = db.cursor()
        cursor.execute(sql_1%param_1)
        db.commit()

        sql_2 = "select id from video where path = '%s'"
        param_2 = (file_path)
        cursor.execute(sql_2%param_2)
        video_id = cursor.fetchone()[0]

        sql_3 = "insert into user_video (user_id, video_id) values(%d, %d)"
        param_3 = (int(user_id), int(video_id))
        cursor.execute(sql_3%param_3)
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400

    return jsonify({'answer': '上传成功'})


# 根据id获取视频列表
@app.route('/list', methods=['GET'])
def getVideoById():
    user_id = request.args.get('user_id')
    page_num = request.args.get('page_num')
    page_size = request.args.get('page_size')
    if user_id == None or page_num == None or page_size == None:
        return jsonify({'error': '数据参数有空值'}), 400
    sql = "select video.* from user_video, video where user_video.video_id = video.id and user_video.user_id = %s limit %s, %s"
    param = (user_id, page_num, page_size)
    try:
        cursor = db.cursor()
        cursor.execute(sql%param)
        results = cursor.fetchall()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400
    
    # 查找不到用户
    if len(results) == 0:
        return jsonify({'error': '用户ID不对啊'}), 400
    
    data = []
    for video in results:
        d = {
            'video_id': video[0],
            'name': video[1],
            'love': video[2],
            'path': video[3]
        }
        data.append(d)
    return jsonify(data)


# 删除视频
@app.route('/del', methods=['DELETE'])
def delVideoById():
    user_id = request.args.get('user_id')
    video_id = request.args.get('video_id')
    if user_id == None or video_id == None:
        return jsonify({'error': '数据参数有空值'}), 400
    sql_1 = "delete from user_video where user_id = %s and video_id = %s"
    param_1 = (user_id, video_id)
    cursor = db.cursor()

    sql_2 = "delete from video where id = %s"
    param_2 = (video_id)
    try:
        cursor.execute(sql_1%param_1)
        count_1 = cursor.rowcount
        if count_1 == 0:
            return jsonify({'error': '找不到指定删除的视频'}), 400
        cursor.execute(sql_2%param_2)
        count_2 = cursor.rowcount
        if count_2 == 0:
            return jsonify({'error': '找不到指定删除的视频'}), 400
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400

    data = {
        'answer': '删除成功'
    }

    return jsonify(data)


# 添加视频到历史中
@app.route('/addHistory', methods=['GET'])
def addVideoToHistory():
    user_id = request.args.get('user_id')
    video_id = request.args.get('video_id')
    if user_id == None or video_id == None:
        return jsonify({'error': '数据参数有空值'}), 400
    
    sql = "insert into history (user_id, video_id) values(%s, %s)"
    param = (user_id, video_id)

    try:
        cursor = db.cursor()
        cursor.execute(sql%param)
        count = cursor.rowcount
        if count == 0:
            return jsonify({'error': 'SQL语句操作失败'}), 400
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400

    data = {
        'answer': '插入成功'
    }
    return jsonify(data)


# 点赞视频
@app.route('/love', methods=['GET'])
def loveVideo():
    video_id = request.args.get('video_id')
    if video_id == None:
        return jsonify({'error': '数据参数有空值'}), 400

    sql = "update video set love = love + 1 where id = %s"
    param = (video_id)
    try:
        cursor = db.cursor()
        cursor.execute(sql%param)
        count = cursor.rowcount
        if count == 0:
            return jsonify({'error': '找不到对应的video_id'}), 400
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'SQL语句操作失败, 参数不对啊,哥'}), 400
    
    data = {
        'answer': '点赞成功'
    }
    return jsonify(data)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
    

