# word_forms
Code and analyses for "Word forms reflect trade-offs between speaker effort and robust listener recognition"

# Download Previously Cached Results for Phonotactic Probability x Frequency Analysis

Bootstrapped results in the `Cross-Linguistic PIC` notebook take a long time to regenerate, even on a machine with many cores (the reference machine has 48). For this reason, we distribute a version with 2500 samples.

`wget -O crosslinguistic_pic3.RData https://www.dropbox.com/s/dc0idpsywx3ra2k/crosslinguistic_pic3.RData?dl=1` 

# Download All Models for Phonotactic Probability x Frequency Analysis (Large)

`wget -O crosslinguistic_pic3.RData https://www.dropbox.com/s/dc0idpsywx3ra2k/10-17-17_GoogleUnigram.zip?dl=1` 

# Regenerate Frequency Data From Scratch

These n-gram models were generated with the [ngrawk2](https://github.com/smeylan/ngrawk2) library, invoked following

`python main.py --ctrl example.ctrl`

The raw datasets are as follows

Google 1T: https://catalog.ldc.upenn.edu/LDC2006T13  
Google Books 2012: http://storage.googleapis.com/books/ngrams/books/datasetsv2.html  
OPUS 2013: https://github.com/smeylan/opus  

# Download Previously Cached Results for Aggregate Competitor Probability x Phonotactic Probability Analysis

TODO

# Regenerate Aggregate Competitor Probability Estimates

This is nontrivial because of the difficulty of installing OpenFST and the compute requirement. If you want to do this:

First, install OpenFST and make sure that the binding library is accessible from your Python environment.

This relies on a wordlist from elsewhere to determine the lexicon, so follow the steps above in "Download All Models for Phonotactic Probability x Frequency Analysis" (called "path to models for prob and freq analysis" below)

`python run.py --run_name test07 --lexicon_path <path to models for prob and freq analysis>/GoogleBooks2012/eng-all/00_lexicalSurprisal/opus_meanSurprisal.csv --output_base_path <directory where you want to output these> --run_from <path to this directory>`
