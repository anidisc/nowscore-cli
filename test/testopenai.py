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