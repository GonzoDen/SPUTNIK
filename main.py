import nltk

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy
import tflearn
import tensorflow
import random
import json
import pickle

from tensorflow.python.framework import ops

with open("intents.json") as file:
    data = json.load(file) #TODO: import json importing another file/ds with for todo upgrading

## extracting data
try:
    #delete pickle.file if you change anything in intents file
    with open("data.pickle", "rb") as f:
        words, labels, training, output = pickle.load(f)
except:
    words = []
    labels = []
    docs_x = [] #what pattern (i)
    docs_y = [] #what tag it's part of

    for intent in data["intents"]:
        for pattern in intent["patterns"]: #pattern == what user asks 
            wrds = nltk.word_tokenize(pattern)
            words.extend(wrds)
            docs_x.append(wrds)
            docs_y.append(intent["tag"])

        if intent["tag"] not in labels:
            labels.append(intent["tag"])

    words = [stemmer.stem(w.lower()) for w in words if w != "?"] #stemming == finding a root of the word, so bot can identify words
    words = sorted(list(set(words))) #removing duplicates

    labels = sorted(labels)

    training = []
    output = []

    out_empty = [0 for _ in range(len(labels))] 

    for x, doc in enumerate(docs_x):
        bag = [] #database for detecting the presence 

        wrds = [stemmer.stem(w.lower()) for w in doc]

        for w in words:
            if w in wrds:
                bag.append(1)
            else:
                bag.append(0)

        output_row = out_empty[:]
        output_row[labels.index(docs_y[x])] = 1

        training.append(bag)
        output.append(output_row)


    training = numpy.array(training)
    output = numpy.array(output)

    with open("data.pickle", "wb") as f:
        pickle.dump((words, labels, training, output), f)

##  developing a model:

ops.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8) #first hidden layer 
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax") #allow us to get probabilities for each output
net = tflearn.regression(net) 

model = tflearn.DNN(net) #training

try:
    model.load("model.tflearn")
except:
## training and saving the model
    model = tflearn.DNN(net)
    model.fit(training, output, n_epoch=1000, batch_size=8, show_metric=True)
    model.save("model.tflearn")

## making predictions
def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
            
    return numpy.array(bag)


def chat():
    print("Start talking with the bot (type quit to stop)!")
    while True:
        inp = input("You: ")
        if inp.lower() == "quit":
            break

        results = model.predict([bag_of_words(inp, words)])
        results_index = numpy.argmax(results)
        tag = labels[results_index]

        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']

        print(random.choice(responses))

chat()

#TODO: if-else or anything like that structure, so Bot can navigate you better
#TODO: figure out data feed