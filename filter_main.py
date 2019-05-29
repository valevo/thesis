# -*- coding: utf-8 -*-

from data.WikiReader import wiki_from_pickles

from Filters.UniformFilterTokens import UniformFilterTokens
from Filters.SpeakerRestrictionFilterRandomised import SpeakerRestrictionFilterRandomised

from collections import Counter
import matplotlib.pyplot as plt
import numpy.random as rand

import os
import pickle
from time import time, asctime

from multiprocessing import Pool, Manager

import argparse

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--filter_type", type=str,
                   help="The type of filter to use. Either `SpeakerRestrictionFilterRandomised`"
                   "or `UniformFilterTokens`.")
    
    args = p.parse_args()
    
    if args.filter_type == "SpeakerRestrictionFilterRandomised":
        return SpeakerRestrictionFilterRandomised, "filters/"
    elif args.filter_type == "UniformFilterTokens":
        return UniformFilterTokens, "uniform/"
    else:
        raise NotImplementedError("No filter with name " + args.filter_type + " is implemented!")


def parallel_filtering(args):
    dir_to_save, shared_sents, cur_j, *filter_args = args
    print(FilterCls.__name__, " with args ", filter_args, "\t(", asctime(), ")",flush=True)
    t0 = time()
    
    cur_seed = int.from_bytes(os.urandom(4), byteorder='little')
    print("\t(Seeded with ", cur_seed, ")", flush=True)
    print("ID", id(shared_sents))
    rand.seed(cur_seed)
    
    cur_filter = FilterCls(shared_sents, *filter_args)
    
    
    filename =  dir_to_save + repr(cur_filter) + "_" + str(cur_j) + ".pkl"

    with open(filename, "wb") as handle:
        print("RESULT WRITTEN INTO ", filename)
        pickle.dump(cur_filter, handle) 
        
    print("DONE WITH", filter_args, cur_j, "(", time() - t0, "secs)", flush=True)
    

def get_length_matched(sents, k):
    sents_list = list(sents)
    perm_sents = rand.permutation(sents_list)

    len_matched_sents = []
    n_toks, cur_i = 0, 0
    
    while n_toks <= k:
        cur_s = perm_sents[cur_i]
        len_matched_sents.append(cur_s)
        n_toks += len(cur_s)
        cur_i += 1
        
    print("LENGTH MATCHED")
    return len_matched_sents

lang = "NO"
wiki = list(wiki_from_pickles("data/" + lang + "_pkl"))
sentences = (s for title, s_ls in wiki for s in s_ls)

k = 5*10**3
length_matched_sents = get_length_matched(sentences, k)

print(len(length_matched_sents), 
      len(set(tuple(s) for s in length_matched_sents)),
      len([w for s in length_matched_sents for w in s]), 
      len(set(w for s in length_matched_sents for w in s)), flush=True)

print("OUTSIDE MAIN")

if __name__ == "__main__":       
    
    FilterCls, save_dir = parse_args()
    
    top_dir = "Results/" + lang + "/"
    if not os.path.isdir(top_dir+save_dir):
        print("MADE DIR ", save_dir, flush=True)
        os.makedirs(top_dir+save_dir)    
         
    print("OUTSIDE MANAGER")
    with Manager() as manager:
        shared_sentences = manager.list(length_matched_sents)
        
        
#        ns = [int(2.5*10**6)]
#        ms = [i**2 for i in range(1, 11)]
#        num_samples = 10
#        j_start_at = 0
        
        ns = [int(10**1)]
        ms = [3]
        num_samples = 5
        j_start_at = 0

    
        if FilterCls is SpeakerRestrictionFilterRandomised:
            params_combined = [(top_dir+save_dir, shared_sentences, j, n, m, "count_tokens") for n in ns 
                               for m in ms for j in range(j_start_at, j_start_at+num_samples)]
        elif FilterCls is UniformFilterTokens:
            params_combined = [(top_dir+save_dir, shared_sentences, j, n) for n in ns 
                               for j in range(j_start_at, j_start_at+num_samples)]
            
        
        print("OUTSIDE POOL")
        with Pool() as p:
            p.map(parallel_filtering, params_combined)
        
    print("\n\nDONE", flush=True)    

