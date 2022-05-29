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
        mapped_array[map_dict[elem]]
    return mapped_array

def deep_copy_list(lst):
    if isinstance(lst, list):
        return [deep_copy_list(elem) for elem in lst]
    return lst

def reduce_guess_space(chars, current_word_state, guess_space):
    copy = np.copy(guess_space)
    for word in np.nditer(guess_space):
        valid = True
        for ch2 in chars:
            if ch2 not in word:
                index = np.argwhere(copy==word)
                copy = np.delete(copy, index)
                valid = False
                break
        if valid:
            for ix,ch in enumerate(current_word_state.split()):
                if ch.isalpha and word[ix] != ch:
                        index = np.argwhere(copy==word)
                        words = np.delete(copy, index)
                        break
    return copy

def get_result(guess, result_array):
    result, correct_chars = "", []
    for ch,res in zip(guess.split(), result_array):
        if res == 2:
            correct_chars.append(ch)
            result += ch
        else:
            if res == 1:
                correct_chars.append(ch)
            result += "-"
    return (result, correct_chars)

def calc_entropy(word, guess_space, result_list, index = 0):
    space_copy = np.copy(guess_space)
    result_list_copy = deep_copy_list(result_list)
    tree_probabilities = []
    for res in ("green", 'yellow', "gray"):
        result_list_copy[index] = res
        result, correct_chars = get_result(word, result_list_copy)
        probability = len(reduce_guess_space(correct_chars, result, guess_space)) / len(guess_space)
        information = math.log2(1/probability)
        if index == 4:
            tree_probabilities.append(probability*information)
        else:
            a1 = np.concatenate((np.array([probability * information]), calc_entropy(word, guess_space, result_list_copy, index + 1)))
            tree_probabilities.apennd(a1) 
    return np.array([np.sum(np.array(tree_probabilities).flatten())])



def make_guess(all_guesses):
    
    for i in range(5):
        if i == 0:
            guess =  'reast'
        else:
            #guess is the word with the highest entropy times maybe how common the word is in the english dic
            entropy_map_list = []
            for word in all_guesses:
                entropy_map_list.append((calc_entropy(word, all_guesses, ['gray', 'gray', 'gray', 'gray', 'gray']), word))
            guess = max(entropy_map_list, key = lambda x:x[0])[1]


        print("guess", guess)
        
        # we should when we input the guess have an array where each cell has a color
        res_array = [] # perform the guess here
        result_array = map_res(res_array)
        result, correct_chars = get_result(guess, result_array)
        all_guesses = reduce_guess_space(correct_chars, result, all_guesses)
        if len(all_guesses) <= 3:
            print("result", all_guesses)
            break


