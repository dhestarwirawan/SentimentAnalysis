import ast
import pandas as pd
import numpy as np
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
import emoji
from googletrans import Translator
from langdetect import detect

file = open("combined_slang_words.txt")
content = file.read()
dicti = ast.literal_eval(content)
slang = pd.DataFrame(dicti.items(),columns=['original','replacement'])

def filters(text):
  final_text = ''
  for word in text.split():
      if word.startswith('@'): #Remove username tag
          continue
      elif word[-3:] in ['com', 'org']: #Remove URL ending with com or org
          continue
      elif word.startswith('pic') or word.startswith('http') or word.startswith('www'):
          continue
      else:
          final_text += word+' '
  return final_text

def remove_emoji(text):
  new_text = emoji.demojize(text)
  new_text = re.sub('[ ]+',' ',text)
  return new_text

def remove_nonalphanumeric(text):
  new_text = re.sub('[^A-Za-z0-9]+',' ',text).lower()
  # remove 2 letter word, \n \t \xe
  shortword = re.compile(r'\W*\b\w{1,2}\b')
  new_text = re.sub(shortword, '', new_text)
  new_text = re.sub('[ ]+',' ',text)
  return new_text

def remove_repeated_char(text):
    return ' '.join([re.sub(r'(.+?)\1+$', r'\1\1',word) for word in text.split(' ')])

translator = Translator()
def trans_to_id(text):
    res = translator.translate(text,src='en',dest='id').text
    return res

def find_en(row, ignore_indexes):
  result = 'no en'
  if row.name in ignore_indexes:
      result = 'no en'
  elif detect(row['content']).lang == 'en':
      result = 'has en'
  else:
      result = 'no en'
  return result

def remove_emo_punc(text):
  text = re.sub('[:_-]+',' ',text)
  return text

slang_dict_map = dict(zip(slang['original'], slang['replacement']))
def normalize_alay(text):
  return ' '.join([slang_dict_map[word] if word in slang_dict_map else word for word in text.split(' ')])

def clean(text):
  text = filters(text)
  text = remove_emoji(text)
  text = remove_nonalphanumeric(text)
  text = remove_repeated_char(text)
  text = normalize_alay(text)
  text = remove_emo_punc(text)
  return text

def translate(df):
  df_cp = df.copy()
  # Find missing index
  df_empty_idx = df_cp['content'].loc[(df_cp['content']=='')|(df_cp['content']==' ')].index
  df_en_res = df_cp.apply(find_en, args=(df_empty_idx,), axis=1)
  df_has_en_mask = (df_en_res == 'has en')
  ### final english indexes
  df_has_en_ix = [i for i,j in enumerate(df_has_en_mask) if j]
  # translate rows that has english (trans_to_id)
  df_en_translated = df_cp['content'].loc[df_has_en_mask].map(trans_to_id)
  # combine translated rows with initial dataframe
  df_cp['content'].loc[df_has_en_ix] = df_en_translated
  return df_cp
