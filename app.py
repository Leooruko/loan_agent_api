from flask import Flask,request,jsonify,render_template
import requests
from utils import promt_llm
import asyncio

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home/",methods=['GET'])
async def home():
    response =await promt_llm(query="Hello, How are you")
    return jsonify({"response": response})

@app.route("/chat",methods=['POST'])
async def chat():
    data = request.get_json()  # await is needed in async context

    promt = data.get("promt")
    if not promt:
        return jsonify({"error": "Missing 'promt' in request"}), 400

    response = await promt_llm(query=promt)
    print(response)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True,port=5500)