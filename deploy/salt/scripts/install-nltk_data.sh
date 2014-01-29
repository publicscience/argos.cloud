#!/bin/bash

# Manually download NLTK data while they sort out the included downloader module.
# https://github.com/nltk/nltk/issues/565

mkdir -p /usr/share/nltk_data
cd /usr/share/nltk_data
for PKG in\
    corpora/wordnet\
    corpora/words\
    corpora/stopwords\
    tokenizers/punkt\
    taggers/maxent_treebank_pos_tagger\
    chunkers/maxent_ne_chunker
do
    wget 'http://nltk.github.com/nltk_data/packages/'$PKG'.zip' -O pkg.zip
    mkdir -p $PKG
    unzip -j pkg.zip -d $PKG
    rm pkg.zip
done
