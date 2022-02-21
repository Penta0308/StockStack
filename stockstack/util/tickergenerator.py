# https://frhyme.github.io/python/python_korean_englished/


def korean_to_be_englished(korean_word):
    """
    한글 단어를 입력받아서 초성/중성/종성을 구분하여 리턴해줍니다. 
    """
    ####################################
    # 초성 리스트. 00 ~ 18
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    # 중성 리스트. 00 ~ 20
    JUNGSUNG_LIST = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ',
                     'ㅣ']
    # 종성 리스트. 00 ~ 27 + 1(1개 없음)
    JONGSUNG_LIST = [' ', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ',
                     'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    ####################################
    r_lst = []
    for w in list(korean_word.strip()):
        if '가' <= w <= '힣':
            ch1 = (ord(w) - ord('가')) // 588
            ch2 = ((ord(w) - ord('가')) - (588 * ch1)) // 28
            ch3 = (ord(w) - ord('가')) - (588 * ch1) - 28 * ch2
            r_lst.append([CHOSUNG_LIST[ch1], JUNGSUNG_LIST[ch2], JONGSUNG_LIST[ch3]])
        else:
            r_lst.append([w])
    return r_lst


def korean_word_to_initials(korean_word):
    """
    한글을 입력받아서 한글 초성에 따라서 이니셜로 변환해줍니다.
    한국 성의 경우 조금 다르게 변환되는데 '박' ==> 'Park'인 부분은 반영하지 않음 
    """
    w_to_k = {'ㄱ': 'K', 'ㄲ': 'G', 'ㄴ': 'N', 'ㄷ': 'D', 'ㄸ': 'D', 'ㄹ': 'R', 'ㅁ': 'M', 'ㅂ': 'B',
              'ㅃ': 'B', 'ㅅ': 'S', 'ㅈ': 'J', 'ㅉ': 'J', 'ㅊ': 'C', 'ㅌ': 'T', 'ㅍ': 'P', 'ㅎ': 'H'}
    r_lst = []
    for i, w in enumerate(korean_to_be_englished(korean_word)):
        if w[0] in w_to_k.keys():
            r_lst.append(w_to_k[w[0]])
        else:
            if w[1] in ['ㅑ', 'ㅕ', 'ㅛ', 'ㅠ', 'ㅖ']:
                r_lst.append('Y')
            elif w[1] in ['ㅝ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅜ', 'ㅞ', 'ㅟ']:
                r_lst.append('W')
            elif w[1] in ['ㅔ', 'ㅡ', 'ㅢ']:
                r_lst.append('E')
            elif w[1] in ['ㅏ', 'ㅐ']:
                r_lst.append('A')
            elif w[1] in ['ㅓ']:
                r_lst.append('U')
            elif w[1] in ['ㅗ']:
                r_lst.append('O')
            elif w[1] in ['ㅣ']:
                if i == 0:
                    r_lst.append('L')
                else:
                    r_lst.append('I')
            else:
                return 'not applicable'
    return "".join(r_lst)
