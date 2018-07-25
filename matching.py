import os
import math
import json
import itertools
import pandas as pd
import collections
import unittest

blog_path = "./blogs/"
path_list = os.listdir(path=blog_path)
BLOG_SAMPLE_SIZE = 10
MAX_SEEN_VALUE = .50
MIN_SEEN_VALUE = .01
MATCH_LENIENCY = .0009

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
    blogs = list(map(get_words, blogs))
    people = [dict(collections.Counter(blog)) for blog in blogs]
    flattened_blogs = [word for blog in blogs for word in blog]
    all_words_seen = dict(collections.Counter(flattened_blogs))
    return remove_useless_words(people, all_words_seen)

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
    return (people, all_words_seen)

def term_frequency(person):
    return .5 + (.5*person/person.max())

# cos_dist = sum(ser1*ser2)/(sqrt(sum(ser1^2)) * sqrt(sum(ser2^2)))
def cos_dist(ser1, ser2):
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
        tdm[person] = term_frequency(tdm[person])
        for i in range(len(person)):
            tdm[person][i] = tdm[person][i] * IDF_Dict[tdm[person].keys()[i]]
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
            if person[relation] < MATCH_LENIENCY: 
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

def runTests():
    # unittest TESTING CLASSES: 
    class test_blog_text_manipulation(unittest.TestCase):
        def setUp(self):
            self.path_list = ["test_file.txt"]
            self.blog_path = "./test_texts/"

        def test_strip_blogs(self):
            self.assertEqual(
                strip_blogs(1, self.blog_path,self.path_list),
                ["this is a test testing testing"],
                "text did not match up"
            )

        def test_get_words(self):
            self.assertEqual(
                get_words("Hello World! Howdy there"),
                ["hello", "world", "howdy", "there"],
                "Did not seperate words correctly"
            )
            
    class test_dict_building_tests(unittest.TestCase):
        def setUp(self):
            self.blogs = strip_blogs(3, "./test_texts/", ["test_file2.txt", "test_file3.txt", "test_file4.txt"])

        def test_build_people(self):
            self.assertEqual(
                build_people_and_find_words(self.blogs),
                ( 
                    [
                        {"trying":1, "still":0, "should":0}
                        , {"still":1, "trying":0, "should":0}
                        , {"should":1, "trying":0, "still":0}
                    ]
                    , {"trying":1, "still":1, "should":1}
                ),
                "people or all_words_seen didn't build correctly"
            )

        def test_remove_useless(self):
            ppl = [
                {"testing":1, "trying":1, "still":0, "should":0}
                , {"testing":1, "still":1, "trying":0, "should":0}
                , {"testing":1, "should":1, "trying":0, "still":0}
            ]
            words = {"testing":3, "trying":1, "still":1, "should":1}
            self.assertEqual(
                remove_useless_words(ppl, words),
                ( 
                    [
                        {"trying":1, "still":0, "should":0}
                        , {"still":1, "trying":0, "should":0}
                        , {"should":1, "trying":0, "still":0}
                    ]
                    , {"trying":1, "still":1, "should":1}
                ),
                "words were not correctly omitted"
            )

    class test_auxiliary_functions(unittest.TestCase):
        def test_cos_dist1(self):
            ser1 = pd.Series([1, 0])
            ser2 = pd.Series([0, 1])
            self.assertEqual(
                cos_dist(ser1, ser2),
                1,
                "cosine value doesn't match up"
            )

        def test_cos_dist2(self):
            ser1 = pd.Series([1, 0])
            ser2 = pd.Series([math.sqrt(2)/2, math.sqrt(2)/2])
            self.assertEqual(
                cos_dist(ser1, ser2),
                1-math.sqrt(2)/2,
                "cosine value doesn't match up"
            )

        def test_term_frequency(self):
            ser = pd.Series([2.0, 3.0, 5.0])
            self.assertEqual(
                list(term_frequency(ser).items()), 
                list((.5 + .5*ser/5).items()), 
                "Series did not adjust correctly"
            )

    class test_json_parsing(unittest.TestCase):
        def setUp(self):
            self.personList = ["9289.male.23.Marketing.Taurus", "4336871.male.17.Automotive.Libra"]

        def test_parse_occupation(self):
            self.assertEqual(
                parse_occupation("9289.male.23.Marketing.Taurus"),
                "Marketing",
                "Did not correctly parse occupation"
            )
        # def test_find_unique_occupations(self):
        #     self.assertEqual(
        #         find_unique_occupations(self.personList),
        #         {"Marketing":0, "Automotive":1},
        #         "did not correctly identify and label unique occupations"
        #     )
    text_manipulation_suite = unittest.TestLoader().loadTestsFromTestCase(test_blog_text_manipulation)
    people_building_suite = unittest.TestLoader().loadTestsFromTestCase(test_dict_building_tests)
    auxiliary_suite = unittest.TestLoader().loadTestsFromTestCase(test_auxiliary_functions)
    json_suite = unittest.TestLoader().loadTestsFromTestCase(test_json_parsing)
    allTests = unittest.TestSuite([text_manipulation_suite, people_building_suite, auxiliary_suite, json_suite])
    unittest.TextTestRunner(verbosity=0).run(allTests)

if __name__ == '__main__':
    runTests()
    blogs = strip_blogs(BLOG_SAMPLE_SIZE, blog_path, path_list)
    (people, all_words_seen) = build_people_and_find_words(blogs)
    tdm = build_tdm(people, all_words_seen)
    # (This step scales really badly)
    similarity_frame = pd.DataFrame({person:{relation:cos_dist(tdm[person], tdm[relation]) for relation in tdm} for person in tdm})
    output_to_json("writeTest.json", path_list, similarity_frame)