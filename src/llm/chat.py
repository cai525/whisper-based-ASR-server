import requests
import json


class ChatBot:

    def __init__(self, api_key, secret_key) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token=" \
            + self.get_access_token()
        self.messages = []
        self.round = 0

    def get_access_token(self):
        url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"\
            .format(api_key=self.api_key, secret_key=self.secret_key)

        payload = json.dumps("")
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}

        response = requests.request("POST", url, headers=headers, data=payload)
        return response.json().get("access_token")

    def request(self, question: str):
        self.messages.append({"role": "user", "content": question})
        payload = json.dumps({"messages": self.messages})
        headers = {'Content-Type': 'application/json'}

        response = requests.request("POST", self.api_url, headers=headers, data=payload)
        answer = response.json().get("result")
        assert isinstance(answer, str)
        self.messages.append({"role": "assistant", "content": answer})
        self.round += 1
        return answer
