// C implementation of the guess scoring function.
#include <string>
using namespace std;

static const int INCORRECT = 0; // Nerdle black: not in the answer.
static const int CORRECT = 1;   // Nerdle green: in the correct spot.
static const int MISPLACED = 2; // Nerdle purple: in the answer, but not in the correct spot.

// This allows us to accommodate Nerdle with up to 8 slots, since this has 16 bits. This cuts down
// storage in half; in the future set to int to solve with more slots.
#define SCORE unsigned short
// Maximum Nerdle expression size.
#define MAX_SLOTS 8

#ifdef __cplusplus
extern "C" SCORE score_guess(const char guess[MAX_SLOTS], const char answer[MAX_SLOTS]) {
#else
SCORE score_guess(const char guess[MAX_SLOTS], const char answer[MAX_SLOTS]) {
#endif
  /*
    Returns the score of a guess.
    A score is an encoded int, where each 2 bits represent a hint (first LSBs = first slot, etc.).
    
    :param guess: Guess string.
    :param answer: Answer string.
    :return: Hint string, coded as a binary number. First 2 LSBs = first slot hint, etc.
    
    Code below uses the assumptions that INCORRECT=0 (the default value of a hint 2-bit pair) and there
    are 2 bits of feedback per hint.
  */
  
  // Iterates through guess and answer lists element-by-element. Whenever it finds a match,
  // removes the value from a copy of answer so that nothing is double counted.
  SCORE hints = 0;
  const size_t num_slots = strlen(answer);
  string answer_no_match(MAX_SLOTS, ' ');
  size_t idx_no_match[MAX_SLOTS];  // Indices of 'guess_no_match' characters.
  int num_no_match = 0;
  
  for (int idx = 0; idx < num_slots; ++idx) {
    char guess_elem = guess[idx];
    char ans_elem = answer[idx];
    if (guess_elem == ans_elem) {
      hints |= (CORRECT << (2 * idx));
    } else {
      answer_no_match[num_no_match] = ans_elem;
      idx_no_match[num_no_match] = idx;
      num_no_match += 1;
    }
  }

  // Misplaced characters are flagged left-to-right, i.e., if there are two misplaced "1"s in the guess and one
  // "1" in the answer, the first "1" in the guess will be misplaced, the second incorrect.
  // Note: only uses the first 'num_no_match' elements in the work arrays.
  // Truncate 'answer_no_match_str' to the first 'num_no_match' elements.
  answer_no_match[num_no_match] = '\0';
  for (int i = 0; i < num_no_match; ++i) {
    int idx = idx_no_match[i];
    char guess_elem = guess[idx];
    int match_idx = answer_no_match.find(guess_elem);
    if (match_idx != string::npos) {
      // Found 'guess_elem' in the not-matched part of the answer.
      hints |= (MISPLACED << (2 * idx));
      answer_no_match.erase(match_idx, 1);
    }
  }

  return hints;
}


// WIP: parallelize a loop over multiple score_guess() calls.
#include <vector>
#include <algorithm>
#include <iostream>

void process(int &n) {
}

#ifdef __cplusplus
extern "C" int parallel_for(int n) {
#else
int parallel_for(int n) {
#endif
  vector<int> nums{3, 4, 2, 8, 15, 267};
  
  auto print = [](const int& n) { cout << " " << n; };
  
  cout << "before:";
  for_each(nums.cbegin(), nums.cend(), print);
  cout << '\n';
  
  for_each(nums.begin(), nums.end(), [](int &n){ n++; });
  
  cout << "after:";
  for_each(nums.cbegin(), nums.cend(), print);
  cout << '\n';
  
  return 0;
  
}

//std::for_each (mydata.begin(), mydata.end(), [&](double d) {
// train(d, net);
//  });
  
