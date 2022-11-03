import pfst
import evaluate
import sys
import pandas as pd
import numpy as np
import argparse
import pickle
import sys
sys.path.append('/home/stephan/python/cmu_pronunciation2')
import cmu_pronunciation2
import os

#python pfst_worker.py --smoothing 0.0 --insertion_cost 1.0 --deletion_scaling 1.0 --lexicon_path /shared_hd1/string-transducer/test00/lexicon.csv --indices_path /shared_hd1/string-transducer/test00/test_indices.csv --model_id smoothing0.0_insertion1.0_deletion1.0 --model_path /shared_hd1/string-transducer/test00/smoothing0.0_insertion1.0_deletion1.0

parser = argparse.ArgumentParser()
parser.add_argument('--lexicon_path', dest='lexicon_path',        type=str, help='file with vocabulary')

parser.add_argument('--indices_path', dest='indices_path',        type=str, help='file with indices in the test')

parser.add_argument('--smoothing', dest='smoothing',        type=float, help='add-minimum smoothing')

parser.add_argument('--insertion_cost', dest='insertion_cost', type=float, help='negative log probability of adding any phoneme')

parser.add_argument('--deletion_scaling', dest='deletion_scaling', type=float, help='scaling factor on the deletion probabilities')

parser.add_argument('--model_id', dest='model_id',        type=str, help='name of the model')

parser.add_argument('--model_path', dest='model_path',        type=str, help='path to store this model')
args = parser.parse_args()

# merge in CMU pronunctiation
cmu = cmu_pronunciation2.CMU_dict()
lexicon_df = pd.read_csv(args.lexicon_path)
lexicon_df = lexicon_df.merge(cmu, left_on='word',right_on='word')


lexicon_df['arpa'] = lexicon_df['cmu_list']
lexicon_df['probability'] = lexicon_df.frequency / np.sum(lexicon_df.frequency)
lexicon_df['unigramSurprisal2'] = [-1. * np.log2(x) for x in lexicon_df['probability']]
# read in the test indices to evaluate
test_indices = pd.read_csv(args.indices_path)['index']

paths = {}
paths['model_path'] = args.model_path

print('Retrieving the likelihood matrix')
likelihood_matrix = evaluate.getAllLikelihoods(lexicon_df, test_indices, args.smoothing, deletion_scaling=args.deletion_scaling, insertion_cost=args.insertion_cost)


print('Saving likelihood matrix')
# pickle.dump( likelihood_matrix.round(5).to_sparse(), open( os.path.join(paths['model_path'], 'likelihoods.pickle'), "wb" )) # if too large
likelihood_matrix.round(10).to_csv(os.path.join(paths['model_path'], 'likelihoods.csv'))

print('Evaluating the likelihood matrix')
scores = evaluate.evaluateLikelihoods(likelihood_matrix, test_indices, lexicon_df, args.smoothing, deletion_scaling=args.deletion_scaling, insertion_cost=args.insertion_cost, model_path = paths['model_path'])

scores.to_csv(os.path.join(paths['model_path'], 'scores.csv'))