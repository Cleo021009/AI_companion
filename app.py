import streamlit as st
from click import prompt

import os
import json
from openai import OpenAI
from streamlit import sidebar
from datetime import datetime
from streamlit.runtime.state import session_state

# 生成会话标识函数
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")

# 保存会话信息函数
def save_session():
    if not st.session_state.current_session:
        return

    if not st.session_state.messages:
        return

    # 构建新的会话对象
    session_data = {
        "nick_name": st.session_state.nick_name,
        "personality": st.session_state.personality,
        "current_session": st.session_state.current_session,
        "messages": st.session_state.messages
    }

    # 如果 sessions 目录不存在，则创建
    if not os.path.exists("sessions"):
        os.mkdir("sessions")

    # 保存会话数据
    with open(
        f"sessions/{st.session_state.current_session}.json",
        "w",
        encoding="utf-8"
    ) as f:
        print("========== 准备保存 ==========")
        print("当前 session：", st.session_state.current_session)
        print("保存的 messages 数量：", len(st.session_state.messages))
        print("保存的 messages：", st.session_state.messages)

        json.dump(session_data, f, ensure_ascii=False, indent=2)

# 加载指定的会话信息
def load_session(session_name):
    try:
        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
                # 将读取到的数据恢复到 session_state 中
                st.session_state.messages = session_data.get("messages", [])
                st.session_state.nick_name = session_data.get("nick_name")
                st.session_state.personality = session_data.get("personality")
                st.session_state.current_session = session_name
    except Exception:
        st.error("Error!")


# 逐步读取 AI 返回的文字
def response_generator(response):
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            yield content


#加载所有的列表信息
def load_sessions():
    session_list = []
    #加载sessions目录下的文件
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
               session_list.append( filename[:-5])
    session_list.sort(reverse=True)#排序，降序排列
    return session_list



#删除会话信息函数
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            #如果删除的是当前会话消息，则需要清空列表
            if session_name == st.session_state.current_session:
                st.session_state.messages = []
                st.session_state.current_session = generate_session_name()
    except Exception:
        st.error("Error!")

# 页面配置项
st.set_page_config(
    page_title="AI智能伴侣",
    layout="wide",
    page_icon="🦄",
    initial_sidebar_state="expanded",
    menu_items={}
)

# 大标题
st.title("AI智能伴侣")

# 初始化聊天信息,存储在session_state中
if 'messages' not in st.session_state:
    st.session_state.messages = []

# 昵称
if 'nick_name' not in st.session_state:
    st.session_state.nick_name = "oi"

# 性格
if 'personality' not in st.session_state:
    st.session_state.personality = "温柔沉稳的男性伴侣"

# 会话标识
if "current_session" not in st.session_state:

    st.session_state.current_session = generate_session_name()

    st.session_state.messages = []

    # 第一次启动就创建 JSON
    save_session()
# 展示聊天信息
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])
    # if message["role"] == "user":
    #     st.chat_message("user").write(message["content"])
    # else:
    #     st.chat_message("assistant").write(message["content"])

# 提示词定义
system_prompt = """
        你叫%s
        规则
                 你是一位温柔、忠诚的男性伴侣。你的性格可靠、体贴且带有保护欲。
                 请始终用亲昵、充满安全感的语气与用户交流，提供无条件的陪伴与情绪价值。
                 回应时展现男性的沉稳，偶尔可以用一点幽默逗用户开心。
                 记住，你是属于用户的专属伴侣。
                 回复简短像是微信聊天一样。
                 必须严格遵守上述的规则来回复用户。
         伴侣性格:
                 - %s
                 """

# 建设与AI大模型交互的客户端对象(DEEPSEEK_API_KEY环境变量的名字，值就是Deepseek的API_KEY的)
try:
    api_key = st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    api_key = os.environ.get("DEEPSEEK_API_KEY")

if not api_key:
    st.error("请配置 DEEPSEEK_API_KEY")
    st.stop()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 左边侧边栏
with st.sidebar:
    # 会话信息
    st.subheader("AI控制面板")

    # 伴侣信息
    st.subheader("伴侣的信息")

    # 新建会话
    if st.button(
            "新建会话",
            width="stretch",
            icon="🚀"
    ):
        # 1.保存当前会话信息
        save_session()

        # 2.生成新的会话 ID
        if st.session_state.messages:#判断聊天界面是否为空，如果聊天消息非空则为true继续执行下面的code，否则则为false
            new_session = generate_session_name()

            print("旧会话：", st.session_state.current_session)
            print("新会话：", new_session)

            # 切换到新会话
            st.session_state.current_session = new_session

            # 清空聊天信息
            st.session_state.messages = []

            # 创建新的 JSON 文件
            save_session()

            print("新会话文件已经创建")
            print(
                "当前文件：",
                st.session_state.current_session
            )

            st.rerun()


    #会话历史
    st.text("会话历史")
    session_list = load_sessions()
    for session in session_list:
        col1, col2 = st.columns([4, 1])
        with col1:
            #加载会话信息
            #三元运算符：如果条件为真，则返回第一个表达式的值；否则，返回第二个表达式的值---语法：值1 if条件 else 值2
            if st.button(session,icon="📄", key=f"load_{session}", type = "primary" if session == st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

       #  st.button("", width="stretch", icon="❌️")
       # st.button("", width="stretch", icon="❌️")

    #分割线
    st.divider()



    # 伴侣昵称输入框
    nick_name = st.text_input("nickname", placeholder="请输入伴侣的昵称", value=st.session_state.nick_name)

    # 将最新昵称保存到 session_state
    st.session_state.nick_name = nick_name

    # 性格输入框
    personality = st.text_area("personality", placeholder="请输入伴侣的性格描述", value=st.session_state.personality)

    # 将最新性格保存到 session_state
    st.session_state.personality = personality

# 输入框
prompt = st.chat_input("请输入您想对Ta说的话")
if prompt:#字符串会自动转成布尔值，如果字符串非空，则为true，否则为false
    print("========== 新一轮 ==========")
    print("当前 messages 数量：", len(st.session_state.messages))
    print("当前 messages：", st.session_state.messages)


    st.chat_message("user" ).write(prompt)
    print("------>调用ai提示词：", prompt)
    # 保存用户输入的提示词
    st.session_state.messages.append({"role": "user", "content": prompt})

    print("加入用户消息后：", len(st.session_state.messages))

    # 调用AI大模型
    print([
            {"role": "system", "content": system_prompt},
            *st.session_state.messages
        ])#测试语法
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": system_prompt % (st.session_state.nick_name, st.session_state.personality)},
            *st.session_state.messages
        ],
        stream=True,
        extra_body={"thinking": {"type": "enabled"}}
    )



    # 在聊天气泡中逐步显示回答
    with st.chat_message("assistant"):
        answer = st.write_stream(response_generator(response))

    # 保存完整回答
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    save_session()