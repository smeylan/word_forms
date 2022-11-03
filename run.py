import pandas as pd
import numpy as np
import sys
sys.path.append('/home/stephan/python/cmu_pronunciation2')
import cmu_pronunciation2
import os
import argparse
import itertools

# example:
#sudo python pfst_worker.py --smoothing 0.0 --insertion_cost 1.0 --deletion_scaling 1.0 --lexicon_path /shared_hd1/string-transducer/test00/lexicon.csv --indices_path /shared_hd1/string-transd ucer/test00/test_indices.csv --model_id smoothing0.0_insertion1.0_deletion1.0 --model_path /shared_hd1/string-transducer/test00/smoothing0.0_insertion1.0_deletion1.0

def dictToBashFlags(dictionary, keys):
    '''convenience function to change dictionary into bash flag of form "--key value"'''
    return(' '.join(['--'+key+ ' '+str(dictionary[key]) for key in keys]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()    
    parser.add_argument('--lexicon_path', dest='lexicon_path',        type=str, help='CSV file with the lexicon')
    parser.add_argument('--run_name', dest='run_name',              type=str, help='name of this run')        
    parser.add_argument('--run_from', dest='run_from',              type=str, help='path to directory with pfst library')        
    parser.add_argument('--output_base_path', dest='output_base_path', type=str, help='location to place the run')        
    #directory structure for output:
    #output_base_path/run_name/modelName
    
    args = parser.parse_args()

    paths = {}
    paths['initial_lexicon_path'] = args.lexicon_path
    paths['output_base_path'] = args.output_base_path
    paths['run_name'] = args.run_name
    paths['run_path'] = os.path.join(paths['output_base_path'], args.run_name)
    paths['lexicon_path'] = os.path.join(paths['run_path'],'lexicon.csv')     
    paths['indices_path'] = os.path.join(paths['run_path'],'test_indices.csv')
    paths['parameters'] = os.path.join(paths['run_path'],'parameters.csv')
    paths['bash_file_path'] = os.path.join(paths['run_path'],'run.sh')    

    if not os.path.exists(paths['run_path']):
        os.makedirs(paths['run_path'])
    
    # load lexicon
    op = pd.read_csv(paths['initial_lexicon_path'])
    # subset to items in CMU
    cmu = cmu_pronunciation2.CMU_dict()
    #op = op.merge(cmu, left_on='token', right_on="word")
    op = op.merge(cmu, left_on='word', right_on="word")    
    op = op.drop(labels=['cmu','cmu_list','flat'], axis=1)

    op = op.drop_duplicates(subset=['word']) # b/c there may be multiple records for a word in CMU
    # write out initial lexicon shared across the different groups        
    op = op.sort_values(by=['frequency'], ascending=False).head(10000)
    op.to_csv(os.path.join(paths['lexicon_path']))    

    # write out the test indices
    # use all iteems as test indices
    #test_indices = range(10) 
    test_indices = range(op.shape[0]) 
    # for sampling a subset of items as test indices
    #test_indices = np.sort(np.random.choice(range(op.shape[0]), 1000, replace=False))   
    pd.DataFrame({'index':test_indices}).to_csv(paths['indices_path'])

    # build the parameter space
    smoothing = [10**-2, 0]
    insertion_cost = [1,3,5,7]
    deletion_scaling = [1,3,5]
    parameters = [smoothing, insertion_cost, deletion_scaling]

    parameter_space = pd.DataFrame(list(itertools.product(*parameters)))
    parameter_space.columns = ['smoothing', 'insertion_cost','deletion_scaling']
    parameter_space.to_csv(paths['parameters'])
        
    bash_commands = []
    bash_commands.append('cd '+args.run_from) 
    for paramSet in parameter_space.to_dict('records'):
        # add a line to the bash script for each worker    
        print(paramSet)
        model_id = 'smoothing'+str(paramSet['smoothing']) +'_insertion'+str(paramSet['insertion_cost'])+'_deletion'+str(paramSet['deletion_scaling'])       

        paths['model_path'] = os.path.join(paths['run_path'], model_id)
        # go ahead and make the folder so there is somewhere to put the log file
        if not os.path.exists(paths['model_path']):
            os.makedirs(paths['model_path'])        

        paths['logPath'] = os.path.join(paths['model_path'],'run.log')

        param_string = dictToBashFlags(paramSet,['smoothing', 'insertion_cost','deletion_scaling'])
        file_string = dictToBashFlags(paths, ['lexicon_path', 'indices_path', 'model_path'])
        bash_command = 'nohup python -u pfst_worker.py '+ param_string + ' ' + file_string + ' --model_id '+ model_id + ' > ' + paths['logPath'] +'  &'
        bash_commands.append(bash_command)

    #if len(bash_commands) > 48:
    #    raise ValueError('Limit parallel runs to the number of virtual cores')    

    bash_test = '\n'.join(bash_commands)
    
    # write out a single file with bash commands
    with open(paths['bash_file_path'], "w") as f:
        f.write(bash_test)

    # execute
    os.system('chmod +x '+paths['bash_file_path'])
    os.system('cd '+paths['run_path']+' && ./run.sh')
