import openai
openai.api_key = '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'
messages = [ {"role": "system", "content":"You are a intelligent assistant."} ]
while True:
   message = input("User : ")
   if message:
      messages.append(
         {"role": "user", "content": message},
      )
      chat = openai.ChatCompletion.create(
         model="gpt-3.5-turbo", messages=messages
      )
   answer = chat.choices[0].message.content
   print(f"ChatGPT: {answer}")
   messages.append({"role": "assistant", "content": answer})