import unittest

from matching import *


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
        self.blogs = list(map(get_words, self.blogs))

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
    # def test_cos_dist1(self):
    #     ser1 = pd.Series([1, 0])
    #     ser2 = pd.Series([0, 1])
    #     self.assertEqual(
    #         cos_dist(ser1, ser2),
    #         1,
    #         "cosine value doesn't match up"
    #     )

    # def test_cos_dist2(self):
    #     ser1 = pd.Series([1, 0])
    #     ser2 = pd.Series([math.sqrt(2)/2, math.sqrt(2)/2])
    #     self.assertEqual(
    #         cos_dist(ser1, ser2),
    #         1-math.sqrt(2)/2,
    #         "cosine value doesn't match up"
    #     )

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


if __name__ == "__main__":
    text_manipulation_suite = unittest.TestLoader().loadTestsFromTestCase(test_blog_text_manipulation)
    people_building_suite = unittest.TestLoader().loadTestsFromTestCase(test_dict_building_tests)
    auxiliary_suite = unittest.TestLoader().loadTestsFromTestCase(test_auxiliary_functions)
    json_suite = unittest.TestLoader().loadTestsFromTestCase(test_json_parsing)
    allTests = unittest.TestSuite([text_manipulation_suite, people_building_suite, auxiliary_suite, json_suite])
    unittest.TextTestRunner(verbosity=2).run(allTests)

