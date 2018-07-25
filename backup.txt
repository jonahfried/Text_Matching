import os
import math
import json
import itertools
import pandas as pd

blog_path = "./blogs/"
path_list = os.listdir(path=blog_path)
BLOG_SAMPLE_SIZE = 11
MAX_SEEN_VALUE = .50
MIN_SEEN_VALUE = .01
MATCH_LENIENCY = .00009

def strip_blogs():
    blogs = []
    for ind in range(BLOG_SAMPLE_SIZE):
        file = open(blog_path+path_list[ind], "rb")
        posts = [line.decode("utf-8", errors="ignore").strip() for line in file]
        posts = [line for line in posts if (line != "" and line[0] != "<")]
        blogs.append(" ".join(posts))
        file.close()
    return blogs

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


def words_and_people_in_blogs(blogs, people, all_words_seen):
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

def remove_useless_words(people, all_words_seen):
    total_people = len(people)
    wordsToRemove = [word for word in all_words_seen if ((all_words_seen[word]/total_people > MAX_SEEN_VALUE) or (all_words_seen[word]/total_people < MIN_SEEN_VALUE))]
    for word in wordsToRemove:
        del all_words_seen[word]
        for person in people:
                if word in person:
                    del person[word]

    for word in [term for term in all_words_seen if term not in wordsToRemove]:
        for person in [d for d in people if word not in d ]:
            person[word] = 0

def build_people_and_find_words(blogs):
    people = []
    all_words_seen = {}
    words_and_people_in_blogs(blogs, people, all_words_seen)
    remove_useless_words(people, all_words_seen)
    return (people, all_words_seen)

def termFrequency(person):
    return .5 + (.5*person/person.max())

# cosDist = sum(ser1*ser2)/(sqrt(sum(ser1^2)) * sqrt(sum(ser2^2)))
def cosDist(ser1, ser2):
    numerator = ser1.dot(ser2)
    ser1_denominator = math.sqrt(sum(map((lambda x: x**2), ser1)))
    ser2_denominator = math.sqrt(sum(map((lambda x: x**2), ser2)))
    return 1 - numerator/(ser1_denominator*ser2_denominator)


def build_tdm(people, all_words_seen):
    tdm = pd.DataFrame({path_list[ind]:people[ind] for ind in range(BLOG_SAMPLE_SIZE) }, dtype=float)

    # (This step scales really badly)
    # IDF_Dict = {}
    # for word in all_words_seen:
    #     personCount = len([person for person in tdm if tdm[person][word] > 0])
    #     if personCount > 0:
    #         IDF_Dict[word] = math.log(BLOG_SAMPLE_SIZE / personCount)
    IDF_Dict = {word:math.log(BLOG_SAMPLE_SIZE/len([person for person in tdm if tdm[person][word] > 0])) for word in all_words_seen}

    for person in tdm:
        tdm[person] = termFrequency(tdm[person])
        for i in range(len(person)):
            tdm[person][i] = tdm[person][i] * IDF_Dict[tdm[person].keys()[i]]
    return tdm

def parse_occupation(path_name):
    return path_name.split(".")[3]

def find_unique_occupations():
    uniques = set([parse_occupation(path) for path in path_list])
    return dict(zip(uniques, range(len(uniques))))

def dict_add_person(nodes_and_links, occupations, person):
        occupation = occupations[person.name.split(".")[3]]
        nodes_and_links["nodes"].append({"id": person.name, "group":occupation})
        for relation in person.keys():
            if person[relation] < MATCH_LENIENCY: 
                nodes_and_links["links"].append({"source":person.name, "target":relation, "value":1})

def output_to_json(write_path, similarity_frame):
    nodes_and_links = {}
    nodes_and_links["nodes"] = []
    nodes_and_links["links"] = []

    occupations = find_unique_occupations()

    for person in similarity_frame:
        dict_add_person(nodes_and_links, occupations, similarity_frame[person])

    file = open(write_path, "w")
    file.write(json.dumps(nodes_and_links, sort_keys=True, indent=2))
    file.close()



if __name__ == '__main__':
    blogs = strip_blogs()
    (people, all_words_seen) = build_people_and_find_words(blogs)
    tdm = build_tdm(people, all_words_seen)
    # (This step scales really badly)
    similarity_frame = pd.DataFrame({person:{relation:cosDist(tdm[person], tdm[relation]) for relation in tdm} for person in tdm})
    output_to_json("writeTest.json", similarity_frame)