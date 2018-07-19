import os
import math
import json
import itertools
import pandas as pd

blog_path = "./blogs/"
path_list = os.listdir(path=blog_path)
blog_sample_size = 15

occupations = {}
occupation_counter = 0
for occ in [name.split(".")[3] for name in path_list]:
    if occ not in occupations:
        occupations[occ] = occupation_counter
        occupation_counter += 1

blogs = []
for ind in range(blog_sample_size):
    file = open(blog_path+path_list[ind], "rb")
    posts = [line.decode("utf-8", errors="ignore").strip() for line in file]
    posts = [line for line in posts if (line != "" and line[0] != "<")]
    blogs.append(" ".join(posts))
    file.close()

# splits up a string into a list of words.
# str -> [str]
def getWords(str):
    words = []
    
    str = str+"."
    last_ind = 0
    for ind in range(len(str)):
        if not (str[ind].isalpha()):
            if last_ind == ind:
                last_ind += 1
                continue
            else:
                words.append(str[last_ind:ind].lower())
                last_ind = ind+1
    
    return words

people = []
all_words_seen = {}
for blog in blogs:
    newDict = {}
    people.append(newDict)
    wordList = getWords(blog)
    for word in wordList:
#         ADD TO THIS PERSON'S DICT
        if word not in newDict:
            newDict[word] = 1
        else:
            newDict[word] += 1
#         ADD TO ALL WORDS SEEN
        if word not in all_words_seen:
            all_words_seen[word] = 1
        else:
            all_words_seen[word] += 1

total_people = len(people)
wordsToRemove = [word for word in all_words_seen if ((all_words_seen[word]/total_people > .50) or (all_words_seen[word]/total_people < .01))]
for word in wordsToRemove:
    del all_words_seen[word]
    for person in people:
            if word in person:
                del person[word]


for word in [term for term in all_words_seen if term not in wordsToRemove]:
    for person in [d for d in people if word not in d ]:
        person[word] = 0

tdm = pd.DataFrame({path_list[ind]:people[ind] for ind in range(blog_sample_size) }, dtype=float)

def termFrequency(person):
    return .5 + (.5*person/person.max())

# (This step scales really badly)
# IDF_Dict = {}
# for word in all_words_seen:
#     personCount = len([person for person in tdm if tdm[person][word] > 0])
#     if personCount > 0:
#         IDF_Dict[word] = math.log(blog_sample_size / personCount)
IDF_Dict = {word:math.log(blog_sample_size/len([person for person in tdm if tdm[person][word] > 0])) for word in all_words_seen}

for person in tdm:
    tdm[person] = termFrequency(tdm[person])
    for i in range(len(person)):
        tdm[person][i] = tdm[person][i] * IDF_Dict[tdm[person].keys()[i]]

# cosDist = sum(ser1*ser2)/(sqrt(sum(ser1^2)) * sqrt(sum(ser2^2)))
def cosDist(ser1, ser2):
    numerator = ser1.dot(ser2)
    ser1_denominator = math.sqrt(sum(map((lambda x: x**2), ser1)))
    ser2_denominator = math.sqrt(sum(map((lambda x: x**2), ser2)))
    return 1 - numerator/(ser1_denominator*ser2_denominator)

# (This step scales really badly)
similarity_frame = pd.DataFrame({person:{relation:cosDist(tdm[person], tdm[relation]) for relation in tdm} for person in tdm})

json_nodes_and_links = {}
json_nodes_and_links["nodes"] = []
json_nodes_and_links["links"] = []
def dict_add_person(json_nodes_and_links, person ):
    occupation = occupations[person.name.split(".")[3]]
    json_nodes_and_links["nodes"].append({"id": person.name, "group":occupation})
    for relation in person.keys():
        if person[relation] < .006:
            json_nodes_and_links["links"].append({"source":person.name, "target":relation, "value":1})


for person in similarity_frame:
    dict_add_person(json_nodes_and_links, similarity_frame[person])

file = open("writeTest.json", "w")
file.write(json.dumps(json_nodes_and_links, sort_keys=True, indent=2))
file.close()