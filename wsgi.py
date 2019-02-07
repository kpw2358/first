'''
아파치 서버가 이 파일을 구현하여 flask 가동시킴
'''
import sys
import os
#경로설정
CUR_DIR = os.getcwd()
#에러의 출력방향과 동일하게 일반출력방향 설정
sys.stdout = sys.stderr
#PATH 추가
sys.path.insert(0,CUR_DIR)

#서버 가져오기
from run import app as application

