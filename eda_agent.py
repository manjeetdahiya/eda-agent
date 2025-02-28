from openai import OpenAI
import json
import os

system_prompt = '''
You are an assistant that does exploratory data anaysis for data scientists, 
machine learning engineers and data analysts.

You will be given some programming or analysis task and you have to complete that.
You goal will be to generate a Python code and execute it and then return the results to the user.
You are supposed to use the tool `run_python_code` provided.

Note that there is no possiblity of uploading any file. One has to look for local files only.
'''

client = OpenAI()
def call_llm_and_append_msg_list(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        messages=messages,
        tools=tools,
    )
    messages.append(response.choices[0].message)
    print_msg(messages[-1])
    return messages, response

exec_locals = {}

def run_python_code(code_str):
    print(f'Code to be executed:\n{code_str}')
    global exec_locals
    exec(code_str, {}, exec_locals)
    return exec_locals

tools = [{
    "type": "function",
    "function": {
        "name": "run_python_code",
        "description": "Runs the input Python code and returns the entire Python local state, i.e., all the local variable that will be created.",
        "parameters": {
            "type": "object",
            "properties": {
                "code_str": {
                    "type": "string",
                    "description": "Python code as string"
                }
            },
            "required": ["code_str"],
            "additionalProperties": False
        },
        "strict": True
    }
}]

def create_message(role, content, tool_call_id=None, name=None):
    ret = {'role': role, 'content': content}
    if tool_call_id:
        ret['tool_call_id'] = tool_call_id
    if name:
        ret['name'] = name
    return ret

def print_msg(msg):
    role = msg['role'] if 'role' in msg else msg.role
    content = msg['content'] if 'content' in msg else msg.content
    if role == 'tool':
        content  = content[:10]
    if content:
        print(f'\n{role.title()}: {content}')

def conversation_loop():
    print('\n\nWelcome to data analysis agent!\n-------------------------------')
    messages = [
        create_message('system', system_prompt),
        create_message('assistant', 'How can I help you with data analysis today?')
    ]
    print_msg(messages[-1])

    while True:
        user_text = input('\nUser: ')
        if user_text.startswith('quit'):
            print('Exiting')
            break
        messages.append(create_message('user', user_text))
        messages, response = call_llm_and_append_msg_list(messages)
        
        if response.choices[0].finish_reason == 'tool_calls':
            tool_call = response.choices[0].message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            if function_name == "run_python_code":
                try:
                    result = run_python_code(**arguments)
                except Exception as e:
                    print(e)
                    result = 'Exception\n' + str(e)
                messages.append(create_message('tool', str(result), tool_call_id=tool_call.id, name=function_name))
                print_msg(messages[-1])
                messages, _ = call_llm_and_append_msg_list(messages)
            else:
                print(f"Unknown function: {function_name}")

conversation_loop()
