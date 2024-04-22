import os
import time
import json
import datetime
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

# pauses symbols
pauses = ".!?;:。！？；："

# default prompt
default_prompt = "You are ChatGPT, a large language model trained by OpenAI. Answer as concisely as possible using the same language to the user"

tools = [
    # function to generate content
    ChatCompletionToolParam({
        "type": "function",
        "function": {
            "name": "generate_content",
            "description": "Generate an image or video based on user input",
            "parameters": {
                "type": "object",
                "properties": {
                    "imageOrVideo": {
                        "type": "integer",
                        "enum": [0, 1],
                        "description": "Decide if you want an image or a video, 0 for image, 1 for video",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Prompt passed to the model, translate to english if needed. e.g. \"A oil painting by Monet, bridge, river.\"",
                    },
                },
                "required": ["imageOrVideo", "prompt"],
            },
        },
    })
]

class ChatGPT:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key)
        # fast and cheap model
        self.fast_and_cheap_model = "gpt-3.5-turbo"
        self.advanced_model = "gpt-4-turbo"
        # initialize parameters, currently not used
        # self.model = "gpt-3.5-turbo"
        # self.max_tokens = 1024
        # self.temperature = 0.7

        # initialize messages
        self.messages = {}
        self.last_time = {}
        self.use_GPT4 = {}
        # use GPT-3.5-turbo by default, use GPT-4 if user sends /gpt4

        # record last time of sending request to openai, prevent too frequent requests
        self.last_time_request = {"time": datetime.datetime.now(), "user_id": None}

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
                system_prompt = default_prompt
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
            self.messages[user_id] = self.messages[user_id][:1] + self.messages[user_id][1 + remove_length :]
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
        return "GPT-4" if self.use_GPT4[user_id] else "gpt-3.5-turbo-16k"

    def check_overload(self, user_id):
        # !TODO find a better way to handle this, currently the reason cause this is unknown
        # check last_time_request, prevent too frequent requests within 2 seconds
        if datetime.datetime.now() - self.last_time_request["time"] < datetime.timedelta(seconds=2):
            # if not the same user, wait for 2 seconds
            if self.last_time_request["user_id"] != user_id:
                time.sleep(2)
                self.last_time_request["time"] = datetime.datetime.now()
                self.last_time_request["user_id"] = user_id
            # if the same user, ingore this request
            else:
                raise Exception("TOOFREQUNET: too frequent requests")
        else:
            self.last_time_request["time"] = datetime.datetime.now()
            self.last_time_request["user_id"] = user_id

    def get_prompt(self, user_message):
        response = self.client.chat.completions.create(
            model=self.fast_and_cheap_model,
            temperature=0.0,
            messages = [self._create_user_prompt(user_message[1:])],
            tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
        if response.choices[0].finish_reason == "tool_calls":
            print("Tools were used to complete the prompt.")
            tool_calls = response.choices[0].message.tool_calls
            for tool_call in tool_calls:
                if tool_call.type == "function":
                    function_arguments = tool_call.function.arguments
                    print(f"function_arguments: {function_arguments}")
                    return eval(function_arguments)
        else:
            print("No tools were used to complete the prompt.")
            return response.choices[0].message.content

    # chat function
    def chat(self, user_id, user_message):
        # decide response interval from 20 to 50.
        interval = max(20, min(len(user_message) // 5, 50))

        # if user_id not in self.messages or over 24 hours, reset chat
        if (user_id not in self.messages) or (
            user_id in self.last_time and self.last_time[user_id] < datetime.datetime.now() - datetime.timedelta(hours=24)
        ):
            pre_answer = "Welcome to ChatGPT! You are in Default Chat Mode\n\n"
            self.reset_chat(user_id, default_prompt)
        else:
            pre_answer = ""

        # send user_message to chatgpt
        self.messages[user_id].append(self._create_user_prompt(user_message))
        # default to use gpt-3.5-turbo
        if user_id not in self.use_GPT4:
            self.use_GPT4[user_id] = False
        # unless set to use gpt-4
        if self.use_GPT4.get(user_id, True):
            model = self.advanced_model
        else:
            model = self.fast_and_cheap_model
        print("Current message: {}".format(str(self.messages[user_id])))
        # !TODO make temperature adjustable to different users.
        completion = self.client.chat.completions.create(model=model, stream=True, messages=self.messages[user_id], temperature=0.7)
        status = ""
        answer = pre_answer + ""
        last_answer = ""

        for c in completion:
            try:
                delta = c.choices[0].delta
                if delta.content != "" and delta.content is not None:
                    status = "streaming"
                    answer += delta.content
                    # only return whole code block
                    if answer.count("```") != 0:
                        continue
                    # set interval to avoid too many requests, and if match the pauses symbol, send the message
                    if len(answer) - len(last_answer) > interval and answer[-1] in pauses:
                        last_answer = answer
                    else:
                        continue
                elif delta.content is None and c.choices[0].finish_reason == "stop":
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
    with open(os.path.join(os.path.dirname(__file__), "config.json"), "r") as f:
        config = json.load(f)
    chatgpt = ChatGPT(config["openai_api_key"])
    user_id = "test"
    user_message = "Hello"

    chatgpt.reset_chat(user_id, default_prompt)
    completion = chatgpt.chat("test", user_message)
    for c in completion:
        print(c)
