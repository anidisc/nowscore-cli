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