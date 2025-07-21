from flask import Flask, jsonify, request
from flask_cors import CORS
from pyngrok import ngrok, conf
import cx_Oracle
import pandas as pd
import os

# 使用 os.path.join 來處理路徑，並確保路徑格式正確
ORACLE_CLIENT_PATH = os.path.abspath(
    r"Z:\跨部門\共用資料夾\C. 業務部\詢價統計DB\Oracle_CLINST\instantclient_23_6"
)

# 設置 Oracle 環境變數
os.environ["PATH"] = ORACLE_CLIENT_PATH + ";" + os.environ["PATH"]
print(os.environ["PATH"])
DATABASE_DNS = "spselect/select@192.168.1.242:1526/sperpdb"

try:
    cx_Oracle.init_oracle_client(lib_dir=ORACLE_CLIENT_PATH)
except Exception as e:
    print(f"Oracle Client 初始化錯誤: {str(e)}")

# 設置 ngrok authtoken
ngrok_auth_token = "2InkEaD5vr8tTt1rVn2DfEkYTr6_5m8a9CybTLjEBumQ5X7KL"  # 請替換成您的 authtoken
conf.get_default().auth_token = ngrok_auth_token

app = Flask(__name__)
# 更新 CORS 配置
CORS(app, resources={
    r"/*": {
        "origins": "*",  # 允許所有來源
        "methods": ["GET", "POST", "OPTIONS"],  # 允許的請求方法
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]  # 允許的請求頭
    }
})

# ngrok 配置
ngrok_tunnel = ngrok.connect(addr="8887", domain="next-conversely-mako.ngrok-free.app")
print('Public URL:', ngrok_tunnel.public_url)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "code": 200,
        "status": "success"
    })

@app.route('/sp_erpdb', methods=['POST'])
def sp_erpdb():
    try:
        # 獲取 form data
        form_data = request.form
        sql = form_data['sql']
        conn = cx_Oracle.connect(DATABASE_DNS, encoding='UTF-8', nencoding='UTF-8')
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [col[0] for col in cursor.description]
        # 轉為 pandas DataFrame

        df = pd.DataFrame(cursor.fetchall(), columns=columns)
        data = df.astype(str).to_dict(orient='records')
        conn.close()
        # 這裡之後可以加入處理 form data 的邏輯
        # 可以通過 form_data.get('key') 來獲取特定的值
        
        return jsonify({
            "status": "success",
            "message": "Data received",
            "data": data  # 轉換 form data 為字典並返回
        })

    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True, port=8887, host='0.0.0.0') 