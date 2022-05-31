from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import keyboard
import numpy as np
import math

#This program is designed to automatically open up and solve the popular wordle game

#load all of the valid wordle guesses and place it in an array
filename = "wordle_answers.txt"
all_guesses = []
with open(filename) as f:
    for line in f:
        all_guesses.append(line.strip())
all_guesses = np.array(all_guesses)


def deep_copy_list(lst):
    """
    This function takes in a list and returns a deep copy of that list
    """
    if isinstance(lst, list):
        return [deep_copy_list(elem) for elem in lst]
    return lst

def reduce_guess_space(chars, incorrect_chars_map, incorrect_mappings, current_word_state, guess_space):
    """
    This function reduces the the possible set of available words that we can use to make a guess on the next turn
    based on the outcome of the current guess.

    Inputs:
        chars: a list of the characters that exist in the correct word
        incorrect_chars_map: a dictionary mapping characters that are not in the correct word
                                to a count of how many times it incorrect appeared in the guess
        incorrect_mappings: a dictionary mapping characters to an index between 0 and 4 inclusive where that character cannot exist in the correct word.
                            Ex. if a is mapped to 3, then the correct word cannot have a as its fourth letter.
        current_word_state: a string shwoing how much of the correct word we currently have. The string contains dashes and characters. Dashes are placed where we
                            have not yet found the correct letter, and letters are only placed in the string after we have correctly found their location. 
                            Ex: 'a--b-. We have correctly found a and b but are still missing the letters in the first, second, and fourth indexes.
        guess_space: The available words we can choose from to make a guess

    Returns:
        copy: The reduced guess space, where all words that would be invalid guesses based on the our current set of information 
        have been removed.
    """
    copy = list(np.copy(guess_space))
    copy = np.array(copy)
    
    for word in np.nditer(guess_space):
        word = str(word)
        for ch1, count in incorrect_chars_map.items():
            # if the letter in the incorrect letter map is not also in the correct letters map
            # we automatically know that the word woudl not be a valid guess
            if ch1 not in chars:
                if ch1 in word:
                    index = np.argwhere(copy==word)
                    copy = np.delete(copy, index)
                    continue # move to next word once we know current word would not be a not a valid future guess
            else: # if the letter is in both the correct list and the incorrect mappings dictionary
                # we know this is a case of having 2 or more of the same letter in our guess
                total = 0
                subtotal = 0
                for c in chars: # get the number of times that letter appears in the correct characters list
                    if c == ch1:
                        subtotal += 1
                for character in word:
                    if character == ch1:
                        total += 1
                        if total == count + subtotal:# if the letter appears too many times in our word the word becomes invalid
                            index = np.argwhere(copy==word)
                            copy = np.delete(copy, index)
                            continue
        
        # if the word does not have one of the valid letters, the word is an invalid guess
        for ch2 in chars:
            if ch2 not in word:
                index = np.argwhere(copy==word)
                copy = np.delete(copy, index)
                valid = False
                continue
           
        # check if the word has a charcter in an invalid location
        for ch3, indexes in incorrect_mappings.items():
            for index2 in indexes:
                if word[index2] == ch3:
                    index = np.argwhere(copy==word)
                    copy = np.delete(copy, index)
                    continue
        
        # if a word does not have the correct letters that have been found, in the correct location, that word is an invalid guess
        for ix,ch in enumerate(list(current_word_state)):
            if ch.isalpha() and word[ix] != ch:
                    index = np.argwhere(copy==word)
                    copy = np.delete(copy, index)
                    continue
    return copy

def get_result(guess, result_array):
    """
    This function takes the result array that contains the result for each letter in our guess, and return
    lists and dictionaries that give us enough information to reduce our current guess space

    Inputs:
        guess: a string representing the word that was guessed
        result_array: a list containing the outcome of each letter in the guess. Present means that
                    the letter exists in the word but not at the index that it was guessed at. Correct
                    indicates that we correctly guessed the letter at its exact index. Absent indicates 
                    that the letter does not exist in the correct word.

    Returns:
        correct_chars: a list of the characters that exist in the correct word
        incorrect_chars_map: a dictionary mapping characters that are not in the correct word
                                to a count of how many times it incorrect appeared in the guess
        incorrect_mappings: a dictionary mapping characters to an index between 0 and 4 inclusive where that character cannot exist in the correct word.
                            Ex. if a is mapped to 3, then the correct word cannot have a as its fourth letter.
        result: a string shwoing how much of the correct word we currently have. The string contains dashes and characters. Dashes are placed where we
                            have not yet found the correct letter, and letters are only placed in the string after we have correctly found their location. 
                            Ex: 'a--b-. We have correctly found a and b but are still missing the letters in the first, second, and fourth indexes.
    """
    result, correct_chars, incorrect_chars_map, incorrect_mapping = "", [], {}, {}
    
    for ix,(ch, res) in enumerate(zip(list(guess), result_array)):
        
        if res == 'correct':
            correct_chars.append(ch)
            result += ch
        
        else:
            if ch not in incorrect_mapping:
                    incorrect_mapping[ch] = [ix]
            else:
                incorrect_mapping[ch].append(ix)
            if res == 'present':
                correct_chars.append(ch)
            else:
                if ch not in incorrect_chars_map:
                    incorrect_chars_map[ch] = 1
                else:
                    incorrect_chars_map[ch] = incorrect_chars_map[ch] + 1
            result += "-"
    
    return (result, correct_chars, incorrect_chars_map, incorrect_mapping)

def calc_entropy(word, guess_space, result_list, index = 0):
    """
    This function calculates the entropy or information revealed by each word in the guess space 
    if we were to guess that word. This allows us to then choose our guess word to be the word that reveals the most information
    Entropy is found by taking the sum of multiplying the probability of guessing the correct answer in the next turn as a result of guesssing a specific word,
    by log base 2 of (1/probability). This is done for every single possible combination of correct, present, and absent that the specific word could have.

    Inputs:
        word: a string representation of the word to be tested
        guess_space: an array of the valid avaialable words we can choose from to make a guess
        result_list: a list representing a hypothetical result of guessing our test word
        index: an integer representing the our current index in the result_list

    """
    tree_probabilities = []
    
    # find probabiltiy and information for every single length 5 permuation of correct, present, and absent
    for res in ("correct", 'present', "absent"):
        result_list_copy = deep_copy_list(result_list)
        result_list_copy[index] = res
        result, correct_chars, incorrect_chars_map, incorrect_mappings = get_result(word, result_list_copy)
        reduced = reduce_guess_space(correct_chars,incorrect_chars_map, incorrect_mappings, result, guess_space)# find out how much information guessing this word would reveal 
        
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



def play_game(all_guesses, guess, result_array):
        """
        This function takes in a guess and result array and returns the reduced guess space array
        """
        result, correct_chars, incorrect_chars_map, incorrect_mappings = get_result(guess, result_array)
        all_guesses = reduce_guess_space(correct_chars, incorrect_chars_map, incorrect_mappings, result, all_guesses)
        index = np.argwhere(all_guesses==guess)
        all_guesses = np.delete(all_guesses, index)
        print("new all guesses", all_guesses) 
        return all_guesses




def make_guess(guess):
    """
    This function types guess into wordle web page
    """
    keyboard.write(guess, .05)
    keyboard.press_and_release('enter')


def game(guess_space):
    """
    This function allows us to automate game play. We open up a web page, and enter in the guesses that our script chooses
    """
    PATH = "C:\Program Files (x86)\chromedriver.exe"
    driver = webdriver.Chrome(PATH)
    driver.get("https://www.nytimes.com/games/wordle/index.html") # open up the wordle page

    def expand_shadow_element(element):# Allows us to retrieve html elements that are in shadow roots
        shadow_root = driver.execute_script('return arguments[0].shadowRoot', element)
        return shadow_root

    shadow_root1 = expand_shadow_element(driver.find_element(By.TAG_NAME,"game-app"))
    root1 = shadow_root1.find_element(By.ID,'game')
    shadow_root2 = expand_shadow_element(root1.find_element(By.TAG_NAME, 'game-modal'))
    button = shadow_root2.find_element(By.CLASS_NAME, "close-icon")
    button.click()


    try:
        game = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "game-app"))
        )
    except:
        pass
    
    time.sleep(2)
    find_game = expand_shadow_element(game)
    board = find_game.find_element(By.ID, 'board')
    rows = board.find_elements(By.TAG_NAME, 'game-row')# get the game board rows
    for i in range(5):
        time.sleep(1)
        
        # get our guess based on the choosing the word that will reveal the most information that
        # will aid our future guesses
        if i == 0:
            guess =  'reast'
        else:
            entropy_map_list = []
            for word in guess_space:
                entropy_map_list.append((calc_entropy(word, guess_space, ['absent', 'absent', 'absent', 'absent', 'absent']), word))
            print("entropy map list", entropy_map_list)
            time.sleep(1)
            guess = max(entropy_map_list, key = lambda x:x[0])[1]
            print(guess)
        make_guess(guess)
    

        row = rows[i]
        row = expand_shadow_element(row)
        tiles = row.find_elements(By.CSS_SELECTOR, "game-tile")
        guess_result = [tile.get_attribute('evaluation') for tile in tiles]# get the result of making a guess from the game board
        
        if guess_result == ['correct', 'correct', 'correct', 'correct', 'correct']: # end script when we have gottent the correct word
            time.sleep(5)
            break
        else:
            guess_space = play_game(guess_space, guess, guess_result)


if __name__ == "__main__":
    game(all_guesses)




