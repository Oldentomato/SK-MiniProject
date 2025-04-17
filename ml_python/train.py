if __name__ == "__main__":
    from data_preprocessing import DataPreProcessing, kindB, kindJ
else:
    from .data_preprocessing import DataPreProcessing, kindB, kindJ
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np
import matplotlib.font_manager as fm
from sklearn.model_selection import GridSearchCV
import joblib


class TrainModel:
    def __init__(self,X_train, X_test, y_train, y_test):
        font_path = 'C:\\windows\\Fonts\\malgun.ttf'
        #font의 파일정보로 font name 을 알아내기
        font_prop = fm.FontProperties(fname=font_path).get_name()
        plt.rc('font', family=font_prop)

        self.gridSearchDict = {
            "n_estimators": [200,300,400],
            "learning_rate": [0.05,0.1,0.2],
            "max_depth": [5,10] #20은 너무 오래걸림
        }


        self.X_train = X_train 
        self.X_test = X_test  
        self.y_train = y_train 
        self.y_test = y_test 


    def trainGrid(self):
        model = xgb.XGBRegressor()
        grid = GridSearchCV(model, param_grid=self.gridSearchDict,scoring="r2", n_jobs=-1, verbose=2) #n_jobs=-1 : 모든 코어 사용
        grid.fit(self.X_train, self.y_train)

        self.model = grid.best_estimator_
        print(f"최적의 파라미터: {grid.best_params_}")

    def train(self):
        self.model = xgb.XGBRegressor(
            n_estimators= 400,
            learning_rate= 0.1,
            max_depth= 10
        )
        self.model.fit(self.X_train, self.y_train)



    def valid(self):
        self.y_pred = self.model.predict(self.X_test)

        mse = mean_squared_error(self.y_test, self.y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(self.y_test, self.y_pred)
        r2 = r2_score(self.y_test, self.y_pred)

        print(f"MSE  : {mse:.2f}") # 실제값과 예측값의 차이의 제곱에 대한 평균
        print(f"RMSE : {rmse:.2f}") # MSE의 Root를 씌운 값
        print(f"MAE  : {mae:.2f}") # 예측값과 실제값의 차이의 절대값에 대한 평균
        print(f"R2   : {r2:.4f}") # 결정계수 예측 값의 분산 비율 (1에 가까울 수록 좋음)

    @staticmethod
    def inferenceModel(modelPath, xData):
        def checkType(var, checkType):
            if type(var) == checkType:
                return True 
            else:
                return False 
        model = joblib.load(modelPath)

        xArr = []
        if (indexNum := kindJ.index(xData.get("자치구명"))) == False:
            raise Exception("자치구명을 찾지 못했습니다")
        else:
            xArr.append(indexNum)

        if (indexNum := kindB.index(xData.get("법정동명"))) == False:
            raise Exception("법정동명을 찾지 못했습니다")
        else:
            xArr.append(indexNum)

        if checkType(xData.get("층"), int):
            xArr.append(xData.get("층"))
        else:
            raise Exception("층 의 int형이 맞지 않습니다")
        
        if checkType(xData.get("임대면적"), float):
            xArr.append(xData.get("임대면적"))
        else:
            raise Exception("임대면적 의 float형이 맞지 않습니다")
        

        if checkType(xData.get("보증금(만원)"), int):
            xArr.append(xData.get("보증금(만원)"))
        else:
            raise Exception("보증금(만원) 의 int형이 맞지 않습니다")
    

        print(xArr)
        return round(model.predict([xArr])[0])


    def save_model(self, path):
        joblib.dump(self.model, path)
        print("model saved")

    
    def show_graph(self):
        xgb.plot_importance(self.model)
        plt.rcParams['figure.figsize'] = [10, 10]
        # plt.show()
        plt.savefig("./ml_python/graph/feature중요도.png")

        plt.figure(figsize=(10, 6))
        plt.scatter(self.y_test, self.y_pred, alpha=0.4, color='dodgerblue')
        plt.plot([self.y_test.min(), self.y_test.max()], [self.y_test.min(), self.y_test.max()], 'r--', lw=2)
        plt.xlabel("실제 임대료 (만원)")
        plt.ylabel("예측 임대료 (만원)")
        plt.title("실제 vs 예측 임대료 비교 (XGBoost)")
        plt.grid(True)
        plt.tight_layout()
        # plt.show()
        plt.savefig("./ml_python/graph/실예측비교도.png")


if __name__ == "__main__":
    dataProcessing = DataPreProcessing("./ml_python/trainData/seoulData.csv")
    X_train, X_test, y_train, y_test = dataProcessing.extract()
    modelTrain = TrainModel(X_train, X_test, y_train, y_test)

    
    modelTrain.train()
    modelTrain.valid()
    modelTrain.show_graph()
    modelTrain.save_model("./ml_python/model/xgb_model2.pkl") 

    # result = TrainModel.inferenceModel("./ml_python/model/xbg_model.pkl",{
    #     "자치구명": "영등포구",
    #     "법정동명": "신도림동",
    #     "층": 7,
    #     "임대면적": 27.01,
    #     "보증금(만원)": 1000
    # })
    # print(f"예상 월 임대료:{result}만원 오차금액 +-20만원")
