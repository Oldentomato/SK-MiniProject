import pandas as pd 
import numpy as np
from sklearn.model_selection import train_test_split
import warnings
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=pd.errors.SettingWithCopyWarning)

kindJ = [
    '강남구', '마포구', '동작구', '광진구', '금천구', '은평구', '구로구', '도봉구', '중구', '중랑구', '성북구', '서대문구',
    '노원구', '서초구', '강서구', '강북구', '송파구', '종로구', '영등포구', '강동구', '관악구', '성동구', '동대문구', '용산구',
    '양천구'
]

kindB = [
    '자곡동','도화동','상도동','화양동','가산동','갈현동','고척동','구로동','방학동','논현동','장충동2가','면목동',
    '삼성동','망우동','동소문동7가','흑석동','합동','공릉동','반포동','마곡동','수유동','진관동','창천동','연남동',
    '응암동','가리봉동','삼전동','명륜2가','여의도동','서초동','오금동','고덕동','대치동','중계동','삼선동2가',
    '천호동','개포동','양평동4가','하월곡동','역삼동','익선동','신림동','행당동','신공덕동','합정동','혜화동',
    '봉천동','미아동','송파동','당산동3가','옥수동','풍납동','연건동','양평동3가','능동','독산동','장지동',
    '장안동','당산동5가','자양동','가양동','방이동','중화동','상봉동','내발산동','대림동','역촌동','공덕동',
    '회기동','율현동','이촌동','구의동','도림동','노량진동','휘경동','정릉동','성내동','가락동','상도1동','신당동',
    '인현동2가','신월동','염리동','동소문동5가','명륜1가','잠원동','사당동','신정동','목동','청파동2가','대현동',
    '세곡동','사근동','창동','우면동','청량리동','용두동','동선동2가','화곡동','마장동','신도림동','개봉동',
    '문정동','노고산동','영등포동1가','등촌동','내수동','상일동','보문동2가','방화동','방배동','대흥동','보문동6가',
    '성수동2가','둔촌동','중동','이문동','군자동','신길동','온수동','문배동','의주로1가','동선동1가','양재동',
    '영등포동4가','잠실동','전농동','남현동','연희동','쌍문동','남가좌동','오류동','석관동','마천동','숭인동',
    '한강로3가','하왕십리동','이태원동','명일동','팔판동','원효로3가','보문동3가','석촌동','광장동','거여동',
    '하계동','양평동5가','제기동','삼선동4가','돈암동','성산동','교북동','상월곡동','수색동','금호동4가','길음동',
    '당인동','망원동','서교동','시흥동','암사동','도봉동','상계동','신사동','대조동','당산동1가','효창동','상암동',
    '안암동1가','안암동5가','황학동','서빙고동','한남동','중곡동','길동','청파동3가','성북동1가','묵동','용답동',
    '월계동','사직동','답십리동','금호동2가','성북동','성수동1가','아현동','우이동','창신동','삼선동1가','충신동',
    '신수동','효제동','불광동','북아현동','중림동','장위동','영등포동7가','안암동2가','홍익동','대방동','송정동',
    '금호동1가','서계동','신천동','당산동4가','삼선동5가','만리동2가','평창동','홍제동','원효로1가','일원동',
    '보문동5가','종암동','신설동','신원동','염창동','당산동6가','번동','응봉동','동소문동4가','영등포동','당산동',
    '명륜3가','광희동1가','항동','신내동','내곡동','충정로3가','압구정동','천왕동','동선동3가','한강로2가',
    '신대방동','양평동2가','동소문동6가','공항동','상수동','청담동','문래동1가','입정동','강일동','도곡동',
    '영등포동8가','증산동','수서동','홍은동','영등포동2가','묵정동','용산동2가','대신동','후암동','미근동','구산동',
    '녹번동','을지로5가','영천동','동선동5가','창전동','무악동','보문동1가','광희동2가','동선동4가','궁동',
    '영등포동3가','삼선동3가','양평동1가','신계동','양평동6가','원효로4가','옥인동','운니동','상왕십리동','북가좌동',
    '본동','회현동1가','정동','보광동','안암동3가','도선동','영등포동6가','신촌동','마포동','용강동','연지동',
    '충무로3가','장충동1가','누상동','현석동','옥천동','가회동','냉천동','안암동4가','사간동','명륜4가','천연동',
    '신창동','동교동','신영동','흥인동','당산동2가','봉원동','평동','문래동6가','충무로5가','도원동','청파동1가',
    '구수동','금호동3가','동숭동','홍파동','동빙고동','동소문동2가','용문동','필동3가','원서동','문래동5가',
    '영등포동5가','필동2가','동소문동1가','오장동','행촌동','염곡동','홍지동','동자동','만리동1가','원효로2가',
    '산천동','이화동','효자동','관수동','부암동','현저동','충정로2가','충무로2가','토정동','순화동','구기동',
    '동작동','저동2가','갈월동','청운동','남영동','누하동','신문로2가','삼청동','문래동3가','남대문로5가',
    '을지로4가','쌍림동','용산동3가','신교동','보문동4가','예장동','계동','보문동7가','원남동','종로5가','인의동',
    '필동1가','원지동','남산동2가','화동','청암동','충무로4가','체부동','회현동2가','종로6가','문래동4가',
    '필운동','개화동','경운동','한강로1가','하중동','문래동2가','무학동','남산동1가','주성동','회현동3가',
    '종로1가','당주동','궁정동','용산동5가','통인동','창성동','을지로6가','외발산동','안국동','남창동','낙원동',
    '관철동','재동','수송동','견지동','북창동','내자동','통의동','남학동','권농동','동소문동3가'

]

class DataPreProcessing:
    def __init__(self, path):
        self.df = pd.read_csv(path, encoding="utf-8")
        self.usecolumns = [ "자치구명", "법정동명", "층",
        "임대면적","보증금(만원)", "임대료(만원)"]
        self.y_column = "임대료(만원)"



    
    def __splitXY(self, x_columns, y_column):
        return self.df[x_columns], self.df[[y_column]]
    
    def __dataNumeric(self, df):
        df['자치구명'] = df['자치구명'].apply(lambda x:kindJ.index(x))
        df['법정동명'] = df['법정동명'].apply(lambda x:kindB.index(x))
        df['층'] = df['층'].apply(lambda x:int(x))

        return df
    

    def __checkYData(self, df, mode="scatter"):
        font_path = 'C:\\windows\\Fonts\\malgun.ttf'
        #font의 파일정보로 font name 을 알아내기
        font_prop = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_prop)

        if mode == "scatter":
            plt.figure(figsize=(12, 6))
            plt.scatter(df.index, df["임대료(만원)"], alpha=0.4, color='dodgerblue')

            plt.title("정답 데이터 (임대료) 분포 - Scatter Plot")
            plt.xlabel("데이터 인덱스")
            plt.ylabel("임대료 (만원)")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig("./ml_python/graph/정답데이터이상치(정상화)2.png")
        elif mode == "boxplot":
            plt.figure(figsize=(12, 6))
            plt.boxplot(df["임대료(만원)"])
            plt.ylabel("임대료 범위")
            plt.savefig("./ml_python/graph/정답데이터boxplot.png")
        else:
            raise Exception("wrong mode name")

        # plt.show()

    
    def __dataCheck(self):
        df_cleaned = self.df.replace('', np.nan)

        invalid_rows = df_cleaned[df_cleaned.isnull().any(axis=1)]

        valid_data = df_cleaned.dropna()

        print("무결성 검사에서 제외된 행 수:", len(invalid_rows))

        before_count = len(self.df)
        after_count = len(valid_data)
        print(f"이전 데이터수: {before_count} \n이후 데이터수: {after_count}")

        print(f"자치구명 종류: {self.df['자치구명'].unique()}")
        print(f"법정동명 종류: {self.df['법정동명'].unique()}")

        self.df = valid_data

    def extract(self):
        self.df = self.df[self.df['전월세구분'] == '월세'] # 월세 데이터만 가져오기
        # self.df = self.df[self.df['임대료(만원)'] < 400] # 정답 데이터의 이상치 제거 
        # 신뢰도 95% 기준 이상치 Index 추출
        outlier = self.df[(abs((self.df['임대료(만원)']-self.df['임대료(만원)'].mean())/self.df['임대료(만원)'].std()))>1.96].index
        # 추출한 인덱스의 행을 삭제하여 clean_df 생성
        self.df = self.df.drop(outlier)

        self.df = self.df[self.usecolumns]
        print(self.df)
        self.__dataCheck()
        x_data, y_data = self.__splitXY(self.usecolumns[:-1], self.y_column)
        x_data = self.__dataNumeric(x_data)

        X_train, X_test, y_train, y_test=train_test_split(x_data,y_data,test_size=0.35,random_state=0)

        print(X_train)
        print(y_train)

        # self.__checkYData(y_train,mode="boxplot")


        return X_train, X_test, y_train, y_test




if __name__ == "__main__":
    data = DataPreProcessing("./ml_python/trainData/seoulData.csv")

    data.extract()