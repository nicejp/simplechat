# lambda/index.py
import json
import os
import boto3
import re
import requests
from botocore.exceptions import ClientError

# APIエンドポイント
API_ENDPOINT = "https://6d3d-34-53-12-247.ngrok-free.app"

def lambda_handler(event, context):
    try:
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # 会話履歴を使用
        messages = conversation_history.copy()
        
        # ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })
        
        # 外部APIへのリクエストペイロードを構築
        request_payload = {
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 512,
                "stopSequences": [],
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        print("Calling external API with payload:", json.dumps(request_payload))
        
        # 外部APIを呼び出し
        response = requests.post(
            f"{API_ENDPOINT}/generate",
            json=request_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # レスポンスを検証
        if response.status_code != 200:
            raise Exception(f"API returned error status code: {response.status_code}, Response: {response.text}")
        
        # レスポンスを解析
        response_body = response.json()
        print("API response:", json.dumps(response_body, default=str))
        
        # 応答の検証
        if not response_body.get('response'):
            raise Exception("No response content from the API")
        
        # アシスタントの応答を取得
        assistant_response = response_body.get('response')
        
        # アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }