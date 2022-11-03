import fst as pyfst
import graphviz
import pandas as pd
import numpy as np
import sets
import time

def atc_w(arpaString, arpa_to_char):
    '''convert ARPA representation to character string'''
    return(''.join([arpa_to_char[x] for x in arpaString]))

def cta_w(charString, char_to_arpa):
    '''convert character string to ARPA representation'''
    return([char_to_arpa[x] for x in charString])

def prepPhonemeConfusionData(smoothing=10**-2, deletion_scaling=1):    
    '''get a matrix appropriate for parameterizing the state machines'''

    print('Preparing confusion matrix table with smoothing='+str(smoothing)+"; deletion_scaling="+str(deletion_scaling))
    ws_c = pd.read_csv('/shared_hd0/datasets/Weber_Smits_Phone_Confusion/Weber_Smits_C_confusion.csv', index_col=0)
    ws_c.loc['ZH','miss'] = .001 #can't be 0
    ws_v = pd.read_csv('/shared_hd0/datasets/Weber_Smits_Phone_Confusion/Weber_Smits_V_confusion.csv', index_col=0)

    #p(d|h) is approximated by p(response phoneme | data)
    # = x[h,d]
    # ws_c.sum(axis=1)
    # rows sum to 100

    ws = pd.concat([ws_c, ws_v])
    ws = ws.fillna(smoothing*100)
    
    initial_deletion_costs = ws.miss / 100.
    updated_deletion_costs = deletion_scaling * initial_deletion_costs
    
    deletionCosts = dict(zip(ws.columns, -1 * np.log2(updated_deletion_costs)))

    initial_remaining_costs =  1. - (ws.miss / 100)
    updated_remaining_costs = 1. - (deletion_scaling * ws.miss / 100.)

    #scaling factor of 2
    # double deletion, need to redistribute the others
    #input: deletion .1, .45 A, .45 B
    #output: deletion: .2, .4 A, .4 B
    if not np.allclose((initial_deletion_costs + initial_remaining_costs), 1):
        print('Failed assertion 1 in deletion scaling')
        import pdb
        pdb.set_trace()

    if not np.allclose((updated_deletion_costs + updated_remaining_costs), 1):
        print('Failed assertion 2 in deletion scaling')
        import pdb
        pdb.set_trace()

    ws = ws.drop(labels=['miss'],axis=1)
    
    normalized = ws.div(ws.sum(axis=1), axis=1)    
    #assert(np.all(normalized.sum(axis=1) == 1))
    rescaled = normalized.multiply(100.*updated_remaining_costs, axis=1)
    
    rescaled = rescaled.div(100)
    #import pdb
    #pdb.set_trace()

    #assert(np.all(rescaled.sum(axis=1).tolist() == updated_remaining_costs))
    rdf = -1 * np.log(rescaled)    
    return rdf, deletionCosts

def make_weighted_flower(phonemeConfusion, deletionCosts, insertionCost):    
    '''make a flower automoton to represent substitutions'''
    def _make_weighted_flower(isyms=None, osyms=None):
        '''dummy function, see below''' 
        epsilon = u'\u03b5' # needs to specify epsilon in this way to allow composition
        if isyms and osyms:
            trans = pyfst.StdTransducer(isyms, osyms)    
        else:    
            trans = pyfst.StdTransducer()    
        
        for phoneme in phonemeConfusion.columns:
            #format: add_arc(src, tgt, labelIn, labelOut weight=None)
            trans.add_arc(0,0,phoneme,phoneme,phonemeConfusion.loc[phoneme,phoneme]) #pyfst.AddArc(0,c,c,0.0,s) #match
            trans.add_arc(0,0,phoneme,epsilon,deletionCosts[phoneme]) #pyfst.AddArc(0,c,epsilon,1.0,s) #deletion
            trans.add_arc(0,0,epsilon,phoneme,insertionCost) #pyfst.AddArc(0,epsilon,c,1.0,s) #insertion
            # get it working without insertions first

            for substitute_phoneme in phonemeConfusion.columns:
                if substitute_phoneme != phoneme :
                    if not np.isinf(phonemeConfusion.loc[phoneme,substitute_phoneme]):
                        trans.add_arc(0,0,phoneme,substitute_phoneme,phonemeConfusion.loc[phoneme,substitute_phoneme])
        
        trans[0].final = 0
        trans.arc_sort_input() # sort labels of second    
        # composition with epsilon should work -- there is explicit provisioning of an epsilon with id 0
        return trans 

    weighted_flower_1 = _make_weighted_flower()  # make once to get the symbol mapping in isyms 
    weighted_flower_2 = _make_weighted_flower(weighted_flower_1.isyms, weighted_flower_1.isyms)  # generate agains with symmetric isyms and osyms
    return(weighted_flower_2)

#@profile
def string_fst(string1, isyms, osyms, icost=0.0, fcost=0.0, ccost=0.0):
    '''make an FST for a string, appropriate for composition'''    
    string_fst = pyfst.StdTransducer(isyms=isyms,osyms=osyms) 
    current_state = 0
    for c in string1:
        next_state = string_fst.add_state() 
        xcost = ccost + (icost if current_state==0 else 0)
        string_fst.add_arc(current_state,next_state,c,c,xcost)
        current_state = next_state    
    string_fst[current_state].final = True
    return(string_fst)     

def checkSymbolTable(a,b):
    '''throw an error if symbol tables for FST's don't align'''
    if a.osyms != b.isyms:
        import pdb
        pdb.set_trace()

#@profile
def getStringFST(arpa_string, arpa_to_char, isyms, osyms):
    '''wrapper for string_fst thatm handles arpa'''
    char_string = atc_w(arpa_string, arpa_to_char)
    fst1 = string_fst(char_string, isyms, osyms)
    fst1.arc_sort_output() # sort labels of first
    return(fst1)

#@profile
def getLikelihood(fst1, fst2, word1, word2, returnType='fst', showTime=False):        
    '''get the minimal distance between fst1 and fst2, corresponding to the log likelihood'''
    
    #limit computing full state transitions to items less than or equal to 4 insertions, substitutions, transitions
    #if pyxdameraulevenshtein.damerau_levenshtein_distance(word1, word2) > 4:
    #    return(np.array([0]))
    # probably want to compose the strings with the FST outside, so I need only do it once

    start_time = time.time()
    
    # Optimized by removing these
    #print('First sym check')
    #checkSymbolTable(fst1,weighted_flower)
    #temp1 = fst1.compose(weighted_flower)    
    #temp1.arc_sort_output() # doesn't change anything
    #print('Second sym check')
    #checkSymbolTable(fst1, fst2)
    temp2 = fst1.compose(fst2) 
    
    shortest = temp2.shortest_path()
    shortest_path = [x for x in shortest.paths()][0]
    shortest_path_length = np.sum([float(y.weight) for y in shortest_path]) 
    
    if showTime:
        print('Elapsed: '+str(time.time() - start_time))
    if returnType == 'best_path':
        return(np.exp(-1.*shortest_path_length))
    elif returnType == 'best_path_log':
        return(shortest_path_length)
    elif returnType == 'shortest_fst':
        return(shortest)
    elif returnType == 'fst':
        #return the composed fst
        return(temp2)
    else:        
        raise ValueError('returnType unrecognized')    

#@profile    
def getLikelihoodsForWord(args):
    '''wrapper to compute the likelihood for all competitors for a word'''
    start_time = time.time()     
    
    i, test_df, competitor_df,  test_to_competitor, fst_collection, wf_fst_collection = args
    print('Processing word: "'+test_df.iloc[i].word+'"')

    #pre-allocate return variable
    rvBest = np.zeros([1, competitor_df.shape[0]])
    # iterating over competitors
    for j in range(competitor_df.shape[0]): # competitor_word 
        likelihood = getLikelihood(wf_fst_collection[j], fst_collection[test_to_competitor[i]], competitor_df.iloc[j].word, test_df.iloc[i].word, returnType='best_path')            
        rvBest[0, j] = likelihood

    print('Elapsed: '+str(time.time() - start_time))
    return(rvBest)
    
def identity(x):
    return x

def extract_array(arrayString, conversionFunction=identity):
    '''convenience function for turning strings back into arrays for pandas CSVs'''
    return(np.array([conversionFunction(x) for x in arrayString[1:len(arrayString)].split(', ')]))         
