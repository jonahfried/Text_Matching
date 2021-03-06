import os
import math
import json
import itertools
import pandas as pd
import collections
import concurrent.futures as cf

blog_path = "./blogs/"
path_list = os.listdir(path=blog_path)
BLOG_SAMPLE_SIZE = 300
MAX_SEEN_VALUE = .50
MIN_SEEN_VALUE = .01
MATCH_LENIENCY = .3

def strip_blogs(sample_size, blog_path, paths):
    blogs = []
    for ind in range(sample_size):
        file = open(blog_path+paths[ind], "rb")
        posts = [line.decode("utf-8", errors="ignore").strip() for line in file]
        posts = [line for line in posts if (line != "" and line[0] != "<")]
        blogs.append(" ".join(posts))
        file.close()
    return blogs

# splits up a string into a list of words.
# str -> [str]
def get_words(str):
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

def build_people_and_find_words(blogs):
    people = [dict(collections.Counter(blog)) for blog in blogs]
    flattened_blogs = [word for blog in blogs for word in blog]
    all_words_seen = dict(collections.Counter(flattened_blogs))
    return remove_useless_words(people, all_words_seen)

def remove_useless_words(people, all_words_seen):
    total_people = len(people)
    words_to_remove = [word for word in all_words_seen if ((all_words_seen[word]/total_people > MAX_SEEN_VALUE) or (all_words_seen[word]/total_people < MIN_SEEN_VALUE))]
    for word in words_to_remove:
        del all_words_seen[word]
        for person in people:
                if word in person:
                    del person[word]

    for word in [term for term in all_words_seen if term not in words_to_remove]:
        for person in [d for d in people if word not in d ]:
            person[word] = 0
    return (people, all_words_seen)

def term_frequency(person):
    return .5 + (.5*person/person.max())

# cos_dist = sum(ser1*ser2)/(sqrt(sum(ser1^2)) * sqrt(sum(ser2^2)))
def cos_dist(ser1, ser2, tdm, square_sums):
    numerator = tdm[ser1].dot(tdm[ser2])
    ser1_denominator = square_sums[ser1]
    ser2_denominator = square_sums[ser2]
    return 1 - numerator/(ser1_denominator*ser2_denominator)

def find_sums_for_each_person(tdm):
    square_sums = {person:math.sqrt(sum(map((lambda x: x**2), tdm[person]))) for person in tdm}
    return square_sums

def find_IDFs(blogs):
    blogs = list(map(set, blogs))
    blogs = list(map(collections.Counter, blogs))
    c = collections.Counter()
    for blog in blogs:
        c += blog
    return {word:math.log(BLOG_SAMPLE_SIZE/c[word]) for word in c}

def build_tdm(people, IDF_Dict, all_words_seen):
    tdm = pd.DataFrame({path_list[ind]:people[ind] for ind in range(BLOG_SAMPLE_SIZE) }, dtype=float)

    # (This step scales really badly)
    # IDF_Dict = {}
    # for word in all_words_seen:
    #     personCount = len([person for person in tdm if tdm[person][word] > 0])
    #     if personCount > 0:
    #         IDF_Dict[word] = math.log(BLOG_SAMPLE_SIZE / personCount)
    

    # for person in tdm:
    #     tdm[person] = term_frequency(tdm[person])
    #     for i in range(len(person)):
    #         tdm[person][i] = tdm[person][i] * IDF_Dict[tdm[person].keys()[i]]
    return tdm

def parse_occupation(path_name):
    return path_name.split(".")[3]

def find_unique_occupations(path_list):
    uniques = set([parse_occupation(path) for path in path_list])
    return dict(zip(uniques, range(len(uniques))))

def dict_add_person(nodes_and_links, occupations, person):
        occupation = occupations[person.name.split(".")[3]]
        nodes_and_links["nodes"].append({"id": person.name, "group":occupation})
        for relation in person.keys():
            if (person[relation] < MATCH_LENIENCY) and (relation != person.name) : 
                nodes_and_links["links"].append({"source":person.name, "target":relation, "value":1})

def output_to_json(write_path, path_list, similarity_frame):
    nodes_and_links = {}
    nodes_and_links["nodes"] = []
    nodes_and_links["links"] = []

    occupations = find_unique_occupations(path_list)

    for person in similarity_frame:
        dict_add_person(nodes_and_links, occupations, similarity_frame[person])

    file = open(write_path, "w")
    file.write(json.dumps(nodes_and_links, sort_keys=True, indent=2))
    file.close()

def main():
    blogs = strip_blogs(BLOG_SAMPLE_SIZE, blog_path, path_list)
    pool = cf.ProcessPoolExecutor()
    blogs = list(pool.map(get_words, blogs))
    (people, all_words_seen) = build_people_and_find_words(blogs)
    IDFs = find_IDFs(blogs)
    tdm = build_tdm(people, IDFs, all_words_seen)
    # (This step scales really badly)
    square_sums = find_sums_for_each_person(tdm)
    similarity_frame = pd.DataFrame({person:{relation:cos_dist(person, relation, tdm, square_sums) for relation in tdm} for person in tdm})
    output_to_json("./output_data/writeTest.json", path_list, similarity_frame)

if __name__ == '__main__':
    main()