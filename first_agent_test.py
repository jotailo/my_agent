AGENT_SYSTEM_PROMPT = """
你是⼀个智能旅⾏助⼿。你的任务是分析⽤户的请求，并使⽤可⽤⼯具⼀步步地解决问题。
# 可⽤⼯具:
- `get_weather(city: str)`: 查询指定城市的实时天⽓。
- `get_attraction(city: str, weather: str)`: 
根据城市和天⽓搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含⼀对Thought和Action：
Thought: [你的思考过程和下⼀步计划]
Action: [你要执⾏的具体⾏动]

Action的格式必须是以下之⼀：
1. 调⽤⼯具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出⼀对Thought-Action
- Action必须在同⼀⾏，不要换⾏
- 当收集到⾜够信息可以回答⽤户问题时，必须使⽤Action: Finish[最终答案] 
格式结束
请开始吧！
"""

import requests

def get_weather(city: str) -> str:
    """
    通过调用wttr.in API 查询真实的天气信息。
    """
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发请求
        response = requests.get(url)
        # 检查状态码
        response.raise_for_status()
        # 解析返回的 JSON 数据
        data = response.json()

        # 提取当前的天气状况
        current_condition = data['current_condition'][0]
        weather_desc = current_condition['weatherDesc'][0]['value']
        temp_c = current_condition['temp_C']

        return f"{city}当前天气:{weather_desc},气温:{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        return f"错误:查询天气时遇到网络问题 - {e}"
    except (KeyError,IndexError) as e:
        return f"错误:解析天气数据失败，可能是城市名无效 - {e}"
import os
from tavily import TavilyClient

def get_attraction(city:str,weather:str) -> str:
    """
    根据城市和天气，使用Tavily Search API 搜索并返回优化后的景点推荐。
    :param city:
    :param weather:
    :return:
    """
    # 获取API密钥
    api_key = "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"
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"

    # 初始化Tavily客户端
    tavily = TavilyClient(api_key=api_key)

    # 3. 构造⼀个精确的查询
    query = f"'{city}' 在'{weather}'天⽓下最值得去的旅游景点推荐及理由"
    try:
        # 4. 调⽤API，include_answer = True会返回⼀个综合性的回答
        response = tavily.search(query=query, search_depth="basic",
                                 include_answer=True)

        # 5. Tavily返回的结果已经⾮常⼲净，可以直接使⽤  # response['answer']是⼀个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]

        #如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results", []):
            formatted_results.append(f"- {result['title']}:{result['content']}")

            if not formatted_results:
                return "抱歉，没有找到相关的旅游景点推荐。"
            return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"错误:执⾏Tavily搜索时出现问题- {e}"


# 将所有⼯具函数放⼊⼀个字典，⽅便后续调⽤
available_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}
from openai import OpenAI


class OpenAICompatibleClient:
    """
    ⼀个⽤于调⽤任何兼容OpenAI接⼝的LLM服务的客户端。
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, prompt: str, system_prompt: str) -> str:
        """
        调⽤LLM API来⽣成回应。
        """
        print("正在调⽤⼤语⾔模型...")
        try:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False
            )
            answer = response.choices[0].message.content
            print("⼤语⾔模型响应成功。")
            return answer
        except Exception as e:
            print(f"调⽤LLMAPI时发⽣错误: {e}")
            return "错误:调⽤语⾔模型服务时出错。"

import re

# --- 1. 配置LLM客户端--
# 请根据您使⽤的服务，将这⾥替换成对应的凭证和地址
API_KEY = "sk-gS0O81mriw5AXm5teosaSKm3GX452MHv8BFQOowiuxYylWdm"
BASE_URL = "https://newapi.rekeymed.com/v1"
MODEL_ID = "deepseek-v4-flash"
TAVILY_API_KEY = "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"
os.environ['TAVILY_API_KEY'] = "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"
llm = OpenAICompatibleClient(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL
)
# --- 2. 初始化--
user_prompt = "你好，请帮我查询⼀下今天北京的天⽓，然后根据天⽓推荐⼀个合适的旅游景点。"
prompt_history = [f"⽤户请求: {user_prompt}"]
print(f"⽤户输⼊: {user_prompt}\n" + " = "*40)
# --- 3. 运⾏主循环   - -
for i in range(5):  #设置最⼤循环次数
    print(f"---循环{i + 1} - --\n")
    # 3.1.构建Prompt
    full_prompt = "\n".join(prompt_history)
    # 3.2.调⽤LLM进⾏思考
    llm_output = llm.generate(full_prompt,system_prompt=AGENT_SYSTEM_PROMPT)
    #模型可能会输出多余的Thought - Action，需要截断
    match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought: | Action: | Observation:) | \Z)', llm_output, re.DOTALL)
    if match:
        truncated = match.group(1).strip()
        if truncated != llm_output.strip():
            llm_output = truncated
            print("已截断多余的Thought - Action对")
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)
    # 3.3.解析并执⾏⾏动
    action_match = re.search(r"Action: (.*)", llm_output, re.DOTALL)
    if not action_match:
        observation = "错误:未能解析到Action字段。请确保你的回复严格遵循'Thought: ... Action: ...'的格式。"
        observation_str = f"Observation: {observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)
        continue
    action_str = action_match.group(1).strip()
    if action_str.startswith("Finish"):
        final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
        print(f"任务完成，最终答案: {final_answer}")
        break
    tool_name = re.search(r"(\w+)\(", action_str).group(1)
    args_str = re.search(r"\((.*)\)", action_str).group(1)
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))
    if tool_name in available_tools:
        observation = available_tools[tool_name](**kwargs)
    else:
        observation = f"错误:未定义的⼯具'{tool_name}'"
    # 3.4.记录观察结果
    observation_str = f"Observation: {observation}"
    print(f"{observation_str}\n" + "=" * 40)
    prompt_history.append(observation_str)