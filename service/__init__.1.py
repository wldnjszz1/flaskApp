'''
 flask 객체 생성
 기본 환경설정
 환경 변수, 디비 초기화
 라우트(블루 프린트)
 라이프사이클(생애주기)
 필터(세션처리)
'''
from flask import Flask, render_template, request, redirect, url_for, session, make_response, jsonify
# 서버 시작점에서부터 패키 경로를 따진다.
from service.model import selectLogin, selectTradeList as stl, selectSearchWithKeyword
from service.model import insertBbsData, selectBbsList
# from service.model import * 하면 예약어 쓸수가 없음 as불가능

# 플라스크 앱 생성
def createApp():
    app = Flask(__name__)
    # 1. 세션 키 생성 => 통상 값은 해쉬값(중복되지 않는 임의값) 사용
    app.secret_key = 'adfad2321fa34dfasdfadfafdff13131kjjlk12' # 사용자가 많지 않으므로 임의로 사용
    initRoute(app)
    return app

# 라우트 초기화 담당
def initRoute(app):
    # 라우트 설정
    @app.route('/')
    def home():
        if not 'uid' in session:  # 세션이 없어도 처음 접근할 수 있는 로그인페이지. 뒤/앞으로가기 버튼 안먹음.
            return redirect(url_for('login'))
        # 로그인 성공 => 쿠키 설정.
        resp = make_response(render_template('index.html')) #세션은 모든곳에서 사용가능 id 정보 들어있음.!!
        # 쿠키 세팅
        resp.set_cookie('uid', session['uid']) #쿠키도 자료구조 딕셔너리!
        return resp #응답을 가로채서 던짐.

    # 로그인
    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method=='GET':
            # 쿠키를 읽어와서 아이디창에 채운다.
            uid = request.cookies.get('uid')
            if not uid: # 쿠키 없으면
                uid = '' #쿠키는 아이디를 들고 있거나 없거나.
            return render_template('login.html',
                    title='데이터 분석관리 로그인',uid=uid)
        else: 
            # 잘 넘어오는지 체크
            uid = request.form.get('uid')
            upw = request.form.get('upw')
            # return uid + " : " + upw
            if not uid or not upw:
                return render_template("alertEx.html", msg='정확하게 입력하세요')
            else:
                row = selectLogin(uid,upw)
                if row: #회원이다
                    # 세션설정(회원이 로그인 했음을 서버가 인지하는 방법)
                    # 간단한 것은 서버 메모리 사용, 통상 고급 -> 디비, 써드파트로 관리
                    # 세션 => 딕셔너리
                    # 세션 생성 // 권한이 없으면 접근을 못함.
                    session['uid'] = uid
                    session['name'] = row['name'] #row에 조회결과 있음//
                    return redirect(url_for('home')) # url은 직접 하드코딩하지 않는다!! redirect('/')=>XX
                else: #회원아니다
                    return render_template("alertEx.html", msg='회원아님')
    
    # 로그아웃
    @app.route('/logout') #로그아웃은 화면이 없고 일만하고 던짐.
    def logout():
        # 세션 없이 접근했을 경우 -> 홈페이지로 리다이렉트
        if not 'uid' in session:  # 세션체크
            return redirect(url_for('home'))
        # 세션제거
        if 'uid' in session:
            session.pop('uid', None) #uid를 제거하면서 반환해줌
        if 'name' in session:
            session.pop('name', None)
        # 홈페이지 리다이렉트
        return redirect(url_for('home'))

    # 주식관리 페이지
    @app.route('/stocks')  # 이요청이 오면 다음으로 처리
    def stocks():
        try:  # http://127.0.0.1:5000/?no=2&amt=10 페이지 이동 가능
            pageNo = int(request.args.get('no'))
            list_len = int(request.args.get('amt'))
        except Exception as e:
            pageNo = 1
            list_len = 10
        rows    = stl(pageNo=pageNo, list_len=list_len)
        return render_template('stocks.html', trades=rows)

    # POST 전용
    @app.route('/search', methods=['POST'])
    def search():  # 아무것도 안쓰면 GET방식..
        # 1. 전달된 데이터 획득 -> print로 출력
        keyword = request.form.get('keyword')  # 키:input태그 속성
        print(keyword)
        # 2. 데이터를 d8로 보내서 쿼리 수행
        rows = selectSearchWithKeyword(keyword)
        if not rows:  # 결과가 없다면
            rows = "{}"
        # 3. 검색 결과를 받아서 json으로 응답(기존 웹화면구성)
        # => 이런식으로 구성된 서버=>미들웨어/어플리케이션서버
        return jsonify(rows)

    # 자료실  (GET 입력화면 + 자료목록 , POST 자료실등록)
    @app.route('/bbs', methods=['GET', 'POST'])
    def bbs():
        if request.method == 'GET':
            return render_template('bbs.html'
                            , rows=selectBbsList())
        else:
            # 1. 데이터 획득
            title       = request.form.get('title')
            contents    = request.form.get('contents')
            author      = session['uid']
            # 파일이 한개일 때, multiple 미사용시
            f           = request.files['files'] #파일 여러개 업로드할때 하나만 뜸
            # 파일이 여러개 업로드 될 떄, multiple 사용시
            files       = request.files.getlist('files')
            print('='*10)
            for file in files: # 파일리스트
                # file : 파일 한개
                print(file.filename)
            print('='*10)

            print(title, contents, author)
            print(f, f.filename)
            # 2. 파일 저장(물리적 디스크)
            # 사용자별로 공간을 줄것인가? => 아이디별 공간 => 저장_시간기록
            # 한공간에 이름을 변조해서 저장할 것인가? => 중복되면 안됨 => 해쉬
            # 저장공간은 서버내 /static/upload
            # 현재 디렉토리 => 
            import os
            # 현재 프로젝트 위치에 따라 경로값이 다르게 나올 수 있다.
            # 운영체계 따라 다르게 나올 수 있다. /// 하드코딩하면 안됨.
            print(os.getcwd()) # 프로젝트폴더에서 작업할 때 가능.!
            save_path = os.path.join(os.getcwd(), 
                        'service','static','upload',f.filename)
            print(save_path)
            # save_path = save_path.replace('\','/')
            # 2. 파일 저장(물리적 디스크)
            # 저장
            f.save(save_path)
            # url 경로
            print('http://127.0.0.1:5000/static/upload/'
                    +f.filename)
            #################################################3
            # 제목, 내용, 작성자, 파일명(다운로드할 수 있는 경로)
            # 콘솔 출력
            # 등록일, 인덱스 번호
            # 3. 디비 저장(해당 글 기록)
            data = {
                "title":title,
                "contents" : contents,
                "author": author,
                "path":"/static/upload/" + f.filename
            }
            msg = None
            url = None
            if insertBbsData(data):
                # 4. 응답(등록되었습니다.) -> 확인 -> /bbs 이동(get)
                msg = "등록 성공"
                url = url_for('bbs')
            else:
                msg = '등록 실패'
            return render_template("alertEx.html", msg=msg ,url=url)
            #######################################################3
            # return ''
            
            
