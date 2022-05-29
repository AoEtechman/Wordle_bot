from contextvars import copy_context
import numpy as np
import csv
import math


filename = "wordle_answers.txt"
all_guesses = []
with open(filename) as f:
    for line in f:
        all_guesses.append(line.strip())
all_guesses = np.array(all_guesses)

def map_res(res_array):
    
    mapped_array = []
    map_dict = {"green": 2, "yellow": 1, "gray": 0}
    for elem in res_array:
        mapped_array.append(map_dict[elem])
    return mapped_array

def deep_copy_list(lst):
    if isinstance(lst, list):
        return [deep_copy_list(elem) for elem in lst]
    return lst

def reduce_guess_space(chars, incorrect_chars, incorrect_mappings, current_word_state, guess_space):
    copy = np.copy(guess_space)
    for word in np.nditer(guess_space):
        word = str(word)
        valid = True
        for ch1 in incorrect_chars:
            if ch1 in word:
                index = np.argwhere(copy==word)
                copy = np.delete(copy, index)
                valid = False
        if valid:
            for ch2 in chars:
                if ch2 not in word:
                    index = np.argwhere(copy==word)
                    copy = np.delete(copy, index)
                    valid = False
                    break
                else:
                    if ch2 in incorrect_mappings:
                        index2 = incorrect_mappings[ch2]
                        if word[index2] == ch2:
                            index = np.argwhere(copy==word)
                            copy = np.delete(copy, index)
                            valid = False
        if valid:
            for ix,ch in enumerate(list(current_word_state)):
                if ch.isalpha() and word[ix] != ch:
                        index = np.argwhere(copy==word)
                        copy = np.delete(copy, index)
                        break
    return copy

def get_result(guess, result_array):
    result, correct_chars, incorrect_chars = "", [], []
    incorrect_mapping = {}
    for ix,(ch, res) in enumerate(zip(list(guess), result_array)):
        if res == 2:
            correct_chars.append(ch)
            result += ch
        else:
            if res == 1:
                correct_chars.append(ch)
                incorrect_mapping[ch] = ix
            else:
                incorrect_chars.append(ch)
            result += "-"
    return (result, correct_chars, incorrect_chars, incorrect_mapping)

def calc_entropy(word, guess_space, result_list, index = 0):
    space_copy = np.copy(guess_space)
    tree_probabilities = []
    for res in ("green", 'yellow', "gray"):
        result_list_copy = deep_copy_list(result_list)
        result_list_copy[index] = res
        result, correct_chars, incorrect_chars, incorrect_mappings = get_result(word, map_res(result_list_copy))
        reduced = reduce_guess_space(correct_chars,incorrect_chars, incorrect_mappings, result, guess_space)
        probability = len(reduced) / len(guess_space)
        if probability == 0:
            information = 0
        else:
            information = math.log2(1/probability)
        if index == 4:
            tree_probabilities.append(probability*information)
        else:
            a1 = np.concatenate((np.array([probability * information]), calc_entropy(word, guess_space, result_list_copy, index + 1)))
            tree_probabilities.append(a1) 
    return np.array([np.sum(np.array(tree_probabilities).flatten())])


def test(answer, guess):
    guess_result = []
    for ch1, ch2 in zip(list(answer), list(guess)):
        if ch1 == ch2:
            guess_result.append('green')
        else:
            if ch2 in answer:
                guess_result.append("yellow")
            else:
                guess_result.append('gray')
    return guess_result


def play_game(all_guesses, answer):
    print("len all Guesses", len(all_guesses))
    for i in range(5):
        if i == 0:
            guess =  'reast'
        else:
            #guess is the word with the highest entropy times maybe how common the word is in the english dic
            entropy_map_list = []
            for word in all_guesses:
                # input()
                # print("word", word)
                entropy_map_list.append((calc_entropy(word, all_guesses, ['gray', 'gray', 'gray', 'gray', 'gray']), word))
            print(entropy_map_list)
            guess = max(entropy_map_list, key = lambda x:x[0])[1]


        print("guess", guess)
        input()
        
        # we should when we input the guess have an array where each cell has a color
        res_array = test(answer, guess) # perform the guess here
        if res_array == ['green'] * 5:
            print("result", guess)
            return guess
        result_array = map_res(res_array)
        result, correct_chars, incorrect_chars, incorrect_mappings = get_result(guess, result_array)
        print(result)
        print(correct_chars)
        all_guesses = reduce_guess_space(correct_chars, incorrect_chars, incorrect_mappings, result, all_guesses)
        index = np.argwhere(all_guesses==guess)
        all_guesses = np.delete(all_guesses, index)
        print("new all guesses", all_guesses)
        if len(all_guesses) <= 3:
            print("result", all_guesses)
            return all_guesses



if __name__ == "__main__":
    play_game(all_guesses, "tiara")