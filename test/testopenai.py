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