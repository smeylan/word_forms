# word_forms
Code and analyses for "Word forms reflect trade-offs between speaker effort and robust listener recognition"

# Download Previously Cached Results

Bootstrapped results in the `Cross-Linguistic PIC` notebook take a long time to regenerate, even on a machine with many cores (the reference machine has 48). For this reason, we distribute a version with 2500 samples.

`wget -O crosslinguistic_pic3.RData https://www.dropbox.com/s/dc0idpsywx3ra2k/crosslinguistic_pic3.RData?dl=1` 

# Download All Models (Large)

`wget -O crosslinguistic_pic3.RData https://www.dropbox.com/s/dc0idpsywx3ra2k/10-17-17_GoogleUnigram.zip?dl=1` 

These n-gram models were generated with the [ngrawk2](https://github.com/smeylan/ngrawk2) library, invoked following

`python main.py --ctrl example.ctrl`

The raw datasets are as follows

Google 1T: https://catalog.ldc.upenn.edu/LDC2006T13  
Google Books 2012: http://storage.googleapis.com/books/ngrams/books/datasetsv2.html  
OPUS 2013: https://github.com/smeylan/opus  
