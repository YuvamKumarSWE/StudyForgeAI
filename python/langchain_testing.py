import getpass
import os

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")


@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

model = ChatGoogleGenerativeAI(model="gemini-flash-latest")

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

# Run the agent
res =  agent.invoke(
    {"messages": [{"role": "user", "content": "what is the weather in sf"}]}
)

print(res.content)



# model_with_search = model.bind_tools([{"google_search": {}}])
# response = model_with_search.invoke("Who is in the group A in FIFA World Cup 2026?")
# print(response.content)