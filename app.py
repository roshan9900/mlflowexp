import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import ElasticNet
from urllib.parse import urlparse
import mlflow
from mlflow.models import infer_signature
import warnings
import sys
import logging

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)

def eval_metrics(actual, pred):
    rmse = np.sqrt(mean_squared_error(actual, pred))
    mae = mean_absolute_error(actual,pred)
    r2 = r2_score(actual, pred)
    return rmse, mae, r2


if __name__=="__main__":
    warnings.filterwarnings('ignore')
    np.random.seed(40)
    
    csv_url = (
        "https://raw.githubusercontent.com/mlflow/mlflow-example/master/wine-quality.csv"
    )
    
    try:
        data = pd.read_csv(csv_url, sep=',')
    except Exception as e:
        logger.exception(
            "Unable to download file, check internet connection"
        )
        
    train, test= train_test_split(data)
    
    train_x = train.drop(['quality'],axis=1)
    test_x = test.drop(['quality'],axis=1)
    
    train_y = train['quality']
    test_y = test['quality']
    
    alpha = float(sys.argv[1]) if len(sys.argv)>1 else 0.5
    l1_ratio = float(sys.argv[2]) if len(sys.argv)>2 else 0.5
    
    with mlflow.start_run():
        lr = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=1)
        lr.fit(train_x, train_y)
        
        predicted_qualities = lr.predict(test_x)

        
        (rmse, mae, r2) = eval_metrics(test_y, predicted_qualities)
        
        print(f'Elasticnet model (alpha={alpha}, l1_ratio = {l1_ratio})')
        print(f"RMSE: {rmse}")
        print(f'MAE: {mae}')
        print(f'R2: {r2}')
        
        mlflow.log_param("alpha",alpha)
        mlflow.log_param('l1_ratio',l1_ratio)
        mlflow.log_metric('rmse',rmse)
        mlflow.log_metric('mae',mae)
        mlflow.log_metric('r2',r2)
        
        predictions = lr.predict(train_x)
        signature = infer_signature(train_x, predictions)
        
        tracking_url_type_store = urlparse(mlflow.get_tracking_uri()).scheme
        
        if tracking_url_type_store!='file':
            mlflow.sklearn.log_model(
                lr, 'model',registed_model_name = 'elasticnet', signature=signature
            )
        else:
            mlflow.sklearn.log_model(lr,'model',signature=signature
                                     )