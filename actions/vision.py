import base64
from actions.scraping import scrape_site, scrape_dexscreener
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


def get_base64_encoded_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def call_vision_model(question, image_path="screenshot.png"):
    vision = ChatOpenAI(model="gpt-4-vision-preview")
    base64_image = get_base64_encoded_image(image_path)
    return vision.invoke(
        [
            SystemMessage(
                content=(
                    """You are a world class vision model that can answer questions in a specific format."""
                )
            ),
            HumanMessage(
                content=[
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "auto",
                        },
                    },
                ]
            ),
        ]
    )


def call_vision_model_on_dexscreener():
    scrape_dexscreener()
    question = "What is in this image? Can you tell me which coins appear in the image? Include just a list of all of them in the response, please."
    return call_vision_model(question, image_path="dexscreener.png")


def navigate_url(url):
    image_path = "screenshot.png"
    scrape_site(url, image_path)
    question = "What is in this image? Extract the information from the image and provide a summary."
    return call_vision_model(question, image_path)
