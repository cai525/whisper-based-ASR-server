import os
import sys

os.chdir("..")
sys.path.append(os.getcwd())

from src.llm.chat import ChatBot


def main():
    with open("./archive/private/llm/api_key", "r") as f:
        api_key = f.read()

    with open("./archive/private/llm/secret_key", "r") as f:
        secret_key = f.read()

    with open("./test/content", "r") as f:
        content = f.read()

    print("The request is: \n{content}".format(content=content))

    bot = ChatBot(api_key, secret_key)
    answer = bot.request(content)
    print(answer)


if __name__ == '__main__':
    main()
