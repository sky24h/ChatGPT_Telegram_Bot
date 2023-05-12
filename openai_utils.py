import json
import openai
import datetime
import os

# pauses symbols
pauses = ',.!?;:、。！？；：'

# default prompt
chat_prompt = "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible using the same language to the user"

class ChatGPT():
    def __init__(self, api_key=None):
        openai.api_key = api_key

        # initialize parameters, currently not used
        # self.model = "gpt-3.5-turbo"
        # self.max_tokens = 1024
        # self.temperature = 0.7

        # initialize messages
        self.messages = {}
        self.last_time = {}
        self.use_GPT4 = {}
        # use GPT-3.5-turbo by default, use GPT-4 if user sends /gpt4

    # create prompts
    def _create_user_prompt(self, user_input):
        return {"role": "user", "content": user_input}

    def _create_chatgpt_answer(self, chatgpt_output):
        return {"role": "assistant", "content": chatgpt_output}

    def _create_system_prompt(self, system_input):
        return {"role": "system", "content": system_input}

    def reset_chat(self, user_id, system_prompt=None):
        if system_prompt is None:
            if user_id not in self.messages or len(self.messages[user_id]) == 0:
                system_prompt = chat_prompt
            else:
                # keep current system prompt
                system_prompt = self.messages[user_id][0]["content"]

        # reset chat
        self.messages[user_id] = []
        self.last_time[user_id] = datetime.datetime.now()
        self.messages[user_id].append(self._create_system_prompt(system_prompt))

    def reduce_messeges(self, user_id, e):
        if len(self.messages[user_id]) > 3:
            # remove half of the messages
            remove_length = (len(self.messages[user_id]) - 1) // 2
            self.messages[user_id] = self.messages[user_id][:1] + self.messages[user_id][1 + remove_length:]
            message = "User: " + str(user_id) + " Forget first two messages to reduce length"
            return False, message
        else:
            raise Exception(error)

    def switch_api(self, user_id):
        self.last_time[user_id] = datetime.datetime.now()
        # if not set, set to True, else switch
        if user_id not in self.use_GPT4:
            self.use_GPT4[user_id] = True
        else:
            self.use_GPT4[user_id] = not self.use_GPT4[user_id]
        return 'GPT-4' if self.use_GPT4[user_id] else 'GPT-3.5-turbo'

    # chat function
    def chat(self, user_id, user_message):
        if (user_id not in self.messages) or (user_id in self.last_time and self.last_time[user_id] < datetime.datetime.now() - datetime.timedelta(hours=24)):
            pre_answer = "Welcome to ChatGPT! You are in Default Chat Mode\n\n"
            self.reset_chat(user_id, chat_prompt)
        else:
            pre_answer = ""

        # send user_message to chatgpt
        self.messages[user_id].append(self._create_user_prompt(user_message))
        # if not set or True, use GPT-3.5-turbo, otherwise use GPT-4
        if not self.use_GPT4.get(user_id, True):
            model = "gpt-4"
        else:
            model = "gpt-3.5-turbo"
        print("Current message: {}".format(str(self.messages[user_id])))
        completion = openai.ChatCompletion.create(model=model, stream=True, messages=self.messages[user_id])
        status = ""
        answer = pre_answer + ""
        last_answer = ""

        for c in completion:
            try:
                delta = c.choices[0].delta
                if "content" in delta:
                    status = "streaming"
                    answer += delta["content"]
                    # gap set to 20 to avoid too many requests, and if match the pauses symbol, send the message
                    if len(answer) - len(last_answer) > 10 and answer[-1] in pauses:
                            last_answer = answer
                    else:
                        continue
                elif delta == {} and c.choices[0].finish_reason == "stop":
                    status = "finished"
                    self.messages[user_id].append(self._create_chatgpt_answer(answer))
                    self.last_time[user_id] = datetime.datetime.now()
                else:
                    # skip
                    continue
                # print(status, answer, len(answer))
                yield status, answer

            except Exception as e:
                raise ValueError("Unexpected ChatGPT response: {} {}".format(c, e))

if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r') as f:
        config = json.load(f)
    chatgpt = ChatGPT(config['openai_api_key'])
    user_id = "test"
    user_message = "Hello"

    chatgpt.reset_chat(user_id, chat_prompt)
    completion = chatgpt.chat("test", "Hello")
    for c in completion:
        print(c)