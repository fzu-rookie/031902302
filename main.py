import re
import sys
from xpinyin import Pinyin


class ac_node(object):

    def __init__(self):
        self.child = dict()
        self.word = ""# 敏感词序列
        self.source = ""# 原敏感词
        self.fail = None
        self.tail = None
        self.length = 0


class ac_tree(object):

    def __init__(self):
        self.root = ac_node()
        self.phrase_list = []  # 相关联的词
        self.spell_mnge = Pinyin()# 用于处理汉字拼音
        self.words_combination = []  # 检测文本的匹配序列
        self.phrase_matrix = []#矩阵

    def prepare_words(self, phrase_combine): # 敏感词列表参数
        # phrase为单个敏感词，未经组合的敏感词
        for index, pha in enumerate(phrase_combine):
            if index == len(phrase_combine) - 1:
                self.str_matrix(pha)
            else:
                self.str_matrix(pha[:-1])
            for single_word in self.phrase_list:
                if index == len(phrase_combine) - 1:
                    self.build_tree(single_word, pha)
                else:
                    self.build_tree(single_word, pha[:-1])
        self.make_fail()


    def str_matrix(self, phrases):# 将敏感词转矩阵
        for single_letter in phrases:
            self.phrase_matrix.append(['[' + self.spell_mnge.get_pinyin(single_letter).replace('-', '') + ']',
                                       self.spell_mnge.get_pinyin(single_letter).replace('-', ''),
                                       str.lower(self.spell_mnge.get_initials(single_letter).replace('-', ''))])
        self.insert_tree(len(phrases))

    def insert_tree(self, layer: int):
        # 递归建树，获取每一行的
        self.loop_Insert(0, layer, "")
        self.phrase_matrix.clear()


    def loop_Insert(self, row_now: int, layer: int, phrase: str):# 递归建树
        if row_now == layer:
            self.phrase_list.append(phrase)
            return
        else:
            for column_now in range(0, 3):
                self.loop_Insert(row_now + 1, layer,phrase + self.phrase_matrix[row_now][column_now])

    def build_tree(self, phrase, initial):
        tmp_root = self.root
        length = 0
        sign = ''
        toge_total = 0
        for i in range(0, len(phrase)):
            if phrase[i] == '[':
                toge_total = True
                continue
            if phrase[i] == ']':
                toge_total = False
                length += 1
                if sign not in tmp_root.child:
                    node = ac_node()
                    node.word = sign
                    tmp_root.child.update({sign: node})
                tmp_root = tmp_root.child[sign]
                sign = ""
                continue
            if toge_total:
                sign += phrase[i]
                continue
            else:
                length += 1
                sign = phrase[i]
                if sign not in tmp_root.child:
                    node = ac_node()
                    node.word = sign
                    tmp_root.child.update({sign: node})
                tmp_root = tmp_root.child[sign]
                sign = ""
        if tmp_root.source == "":
            tmp_root.source = initial
        tmp_root.length = length

    def make_fail(self):
        temp_list = [self.root]
        while len(temp_list) != 0:#遍历
            pre_root = temp_list.pop(0)
            for key, value in pre_root.child.items():
                if pre_root == self.root:
                    pre_root.child[key].fail = self.root
                else:
                    point = pre_root.fail
                    while point is not None:
                        if key in point.child:
                            pre_root.child[key].fail = point.fail
                            break
                        point = point.fail
                    if point is None:
                        pre_root.child[key].fail = self.root
                temp_list.append(pre_root.child[key])
    def search_senten(self, sentence, line):
        index_list = []
        temp = self.root
        for index, letter in enumerate(sentence):
            if self.illegal_word(letter):
                continue
            letter = self.spell_mnge.get_pinyin(letter).replace('-', '')
            while temp.child.get(str.lower(letter)) is None and temp.fail is not None:
                temp = temp.fail
            if temp.child.get(str.lower(letter)) is not None:
                temp = temp.child.get(str.lower(letter))
            else:
                continue
            if temp.length:
                af_start = self.match_word(node=temp, sentence=sentence, position=index, line=line)
                if len(index_list):
                    if af_start == index_list[len(index_list) - 1]:
                        self.words_combination.pop(len(self.words_combination) - 2)
                index_list.append(af_start)

    def match_word(self, node, sentence, position, line: int) -> int:
        matched_part = ""
        word_length = node.length
        while word_length:
            if self.illegal_word(sentence[position]):# 忽略非法字符
                matched_part = matched_part + sentence[position]
            else:
                matched_part = matched_part + sentence[position]
                word_length -= 1
            position -= 1
        matched_part = matched_part[::-1]
        for letter in matched_part:
            number = bool(re.search(r'\d', matched_part))
            if number:
                return -1
        self.words_combination.append("Line" + str(line) + ": <" + node.source + "> " + matched_part)
        return position

    @staticmethod
    def illegal_word(letter) -> bool:
        if letter in "0123456789[\"`~!@#$%^&*()+=|{}':;',\\.<>/?~！@#￥%……&*（）——+| {}【】‘；：”“’。，、？_] \n":
            return True
        return False

    def write_file(self, file_name):
        f = open(file_name, "a", encoding="utf-8")
        f.write("Total: " + str(len(self.words_combination)) + "\n")
        for element in self.words_combination:
            f.write(element + "\n")
        f.close()
        pass

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("error")
        exit(-1)
    model = ac_tree()
    word_path = sys.argv[1]
    org_path = sys.argv[2]
    ans_path = sys.argv[3]
    word_file = open(word_path, encoding='utf-8')
    org_file = open(org_path, encoding='utf-8')
    sw = word_file.readlines()
    org = org_file.readlines()
    word_list = []
    for line in sw:
        line = line.strip()
        word_list.append(line)
    model.prepare_words(word_list)
    for xs in org:
        model.search_senten(str(xs), org.index(xs) + 1)
    model.write_file(ans_path)
    word_file.close()
    org_file.close()