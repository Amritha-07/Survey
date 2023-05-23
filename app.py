from flask import Flask, render_template, request
import numpy as np
import pandas as pd
import os
import nltk
import mysql.connector
from collections import Counter

# my sql connection
mysql = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "",
    port = "3306",
    database = "survey"
)

i = 0
lt = []
phone = "model"
gtext = ""
rlt = []
sentiment = 0
summary = ""


from nltk.corpus import stopwords
stop_words = set(stopwords.words('english'))
from nltk.stem.wordnet import WordNetLemmatizer 
lem = WordNetLemmatizer()
from nltk.stem.porter import PorterStemmer 
stem = PorterStemmer()
from nltk import word_tokenize, pos_tag
corpus = set()
new_corpus = []

import openai
openai.api_key = "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"

questions = ['camera','speed','battery','display','fingerprint','audio','storage', 'calls', 'price']

def insert():
    global phone
    global sentiment
    global rlt
    global gtext
    global summary
    completion = openai.Completion.create(engine="text-davinci-003", prompt= f"summarize the key notes in {summary}",max_tokens=1000)    
    summary = completion.choices[0]['text']
    mycursor = mysql.cursor()
    sql = "insert into review(phone,general,features,camera,speed,battery,display,fingerprint,audio,storage,calls,price,summary) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    val = (phone,sentiment,gtext,rlt[0],rlt[1],rlt[2],rlt[3],rlt[4],rlt[5],rlt[6],rlt[7],rlt[8],summary)
    mycursor.execute(sql,val)
    mysql.commit()


def clean_text(input_text):
    input_text = str(input_text)
    words = input_text.split() 
    noise_free_words = [lem.lemmatize(word, "v") for word in words if word not in stop_words] 
    noise_free_text = " ".join(noise_free_words) 
    return noise_free_text

def find_sentiment(text_input):
    score = 0 
    text_input = text_input.split()
    f = open('pos.txt', 'r')
    x = f.read()
    x = x.split()
    f1 = open('neg.txt', 'r')
    y = f1.read()
    y = y.split()
    for i in text_input:
        if i in x:
            score = score + 1
        if i in y:
            score = score - 1
    return int(score)

def addToUser(text):
    f = open("sql.txt", "w")

def generateQuestions(text):
    global sentiment
    data = clean_text(text)
    sentiment = find_sentiment(data)
    features = filter_features(data)
    features_cnt = Counter(new_corpus)
    common_features = features_cnt.most_common(50)
    res_features = list(features.split())
    featurez=[]
    a = ['camera','speed','battery','display','fingerprint','audio','storage', 'calls', 'price']
    for i in res_features:
        if i.lower() in a:
            featurez.append(i)
    featurez = list(set(featurez))
    if sentiment > 0:
        sentimentz = 'positive'
    else:
        sentimentz = 'negative'
    l = []
    for i in featurez:
        completion = openai.Completion.create(engine="text-davinci-003", prompt= f"frame 2 questions to ask customer when they give {sentimentz} review about mobile {featurez[0]}",max_tokens=1000)    
        li=(completion.choices[0]['text'])
        li = li.split("\n")
        li.pop(1)
        li.pop(0)
        l = l + li
    for i in range(len(l)):
        l[i] = l[i][3:]
    return l


def filter_features(text):
    tokens = word_tokenize(text)
    tokens = pos_tag(tokens)
    tokens = [word for word, pos in tokens if pos in ['NN']]
    corpus.update(tokens)
    new_corpus.extend(tokens)
    res = " ".join(tokens)
    return res

app = Flask(__name__)
app.static_folder = 'static'

def reply(userText, i):
    global lt
    global rlt
    global summary
    if i > len(lt):
        rlt.append(min(5, int(userText)))
    if i > 1 and i <= len(lt):
        summary += " " + lt[i-2]
        summary += " " + userText
    if i == 0:
        mobile = str(userText)
        phone = mobile
        completion = openai.Completion.create(engine="text-davinci-003", prompt= f"frame question to ask customer to give general review {mobile} phone expect rating questions",max_tokens=1000)    
        return completion.choices[0]['text']
    elif i < len(lt):
        return lt[i-1]
    elif i >= len(lt) and i <= len(lt) + 8:
        attribute = questions[i-len(lt)]
        completion = openai.Completion.create(engine="text-davinci-003", prompt= f"frame question to ask customer to rate {attribute} of mobile phone out of 5",max_tokens=1000)    
        return completion.choices[0]['text']   
    else:
        insert()
        return "Thank you for your feedback"
        

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    global i
    global lt
    global gtext
    userText = request.args.get('msg')
    if i == 1:
        gtext = userText
        lt = generateQuestions(userText)
        print(lt)
    res = reply(str(userText), i)
    i += 1
    return str(res)

if __name__ == "__main__":
    app.run() 
