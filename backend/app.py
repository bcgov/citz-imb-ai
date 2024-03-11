#listening for queries. (API endpopint)
#save qwuery and append to file/db
#convert the query to embeddings
#searches the embedding in the db
#gets the ressult
#save the result to the file/db
#sends it to the mdoel
#gets result
#saves the result to the file/db
#sends it to the user

from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_geek():
    return '<h1>Hello from Flask & Docker</h2>'


if __name__ == "__main__":
    app.run(debug=True)