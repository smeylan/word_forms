import csv
import pandas as pd
from string import digits
import sys

def parse_cmu(line, digit_remover=None, digits=None, removeAccentMarkers=True):
    if removeAccentMarkers:
        #line =line.translate(None, digits) #Python 2

        if digit_remover is not None:
            line = line.translate(digit_remover) # Python 3 solution
        elif digits is not None: 
            line = line.translate(None, digits) # Python 2                    
        else:
            raise ValueError('Either specify digit remover or digits')

    else:        
        pass
    split_line = line.split('  ')
    if len(split_line) != 2:
        return({'word':split_line[0].lower(),'cmu':None})
    transcription = split_line[1]

    syllables = transcription.split(' - ')

    syl_transcript = [x.split(' ') for x in syllables]
                
    return({'word':split_line[0].lower(),'cmu':syl_transcript})

def CMU_dict():
    cmu_raw = pd.read_table('/shared_hd0/corpora/CMU_pronunciation/cmudict_syllabified.txt', sep='\t', header=None, quoting=csv.QUOTE_NONE)
    cmu_raw.columns = ['line']

    if sys.version_info.major == 3:        
        digit_remover = str.maketrans('','',digits) 
        cmu = pd.DataFrame([parse_cmu(x, digit_remover=digit_remover) for x in cmu_raw.line])
    
    elif sys.version_info.major == 2:
        cmu = pd.DataFrame([parse_cmu(x, digits=digits) for x in cmu_raw.line])
        
    
    cmu['flat'] = [' '.join([item for sublist in l for item in sublist]) if l is not None else None for l in cmu.cmu ]
    cmu['cmu_list'] = [x.split(' ') if x is not None else None for x in cmu.flat]
    return(cmu)