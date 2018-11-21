# language-learning/src/learner.py                                      # 81121
import os
from copy import deepcopy
import pickle, numpy as np, pandas as pd
from shutil import copy2 as copy
from IPython.display import display
from collections import OrderedDict, Counter
from .widgets import html_table
from .utl import UTC, kwa
from .read_files import check_dir, check_mst_files
from .pparser import files2links
from .category_learner import learn_categories, add_disjuncts, cats2list
from .grammar_inducer import induce_grammar
from .generalization import generalize_categories, generalize_rules, \
                            generalise_rules                            # 81120
from .write_files import list2file, save_link_grammar, save_cat_tree

__all__ = ['learn_grammar']


def learn_grammar(**kwargs):
    log = OrderedDict({'start': str(UTC()), 'learn_grammar': 'v.0.7.81109'})
    input_parses = kwargs['input_parses']
    output_grammar = kwargs['output_grammar']
    output_categories = kwa('', 'output_categories', **kwargs)
    output_statistics = kwa('', 'output_statistics', **kwargs)
    temp_dir = kwa('', 'temp_dir', **kwargs)
    if os.path.isdir(output_grammar):
        prj_dir = output_grammar
    else:
        prj_dir = os.path.dirname(output_grammar)
    log.update({'project_directory': prj_dir})
    if output_categories == '':
        output_categories = prj_dir
    if output_statistics != '':  # TODO: check path: filename/dir?
        corpus_stats_file = output_statistics
    else:
        corpus_stats_file = prj_dir + '/corpus_stats.txt'
    if temp_dir != '':
        if os.path.isdir(temp_dir):
            kwargs['tmpath'] = temp_dir

    context = kwa(1, 'context', **kwargs)
    clustering = kwa('kmeans', 'clustering', **kwargs)  # TODO: update
    cats_gen = kwa('off', 'categories_generalization', **kwargs)
    grammar_rules = kwa(1, 'grammar_rules', **kwargs)
    verbose = kwa('none', 'verbose', **kwargs)

    files, re01 = check_mst_files(input_parses, verbose)
    log.update(re01)
    kwargs['input_files'] = files
    links, re02 = files2links(**kwargs)
    log.update(re02)
    list2file(re02['corpus_stats'], corpus_stats_file)
    log.update({'corpus_stats_file': corpus_stats_file})

    categories, re03 = learn_categories(links, **kwargs)
    log.update(re03)

    '''Generalize word categories'''

    if cats_gen == 'jaccard' or (cats_gen == 'auto' and clustering == 'group'):
        categories, re04 = generalize_categories(categories, **kwargs)
        log.update(re04)
    elif cats_gen == 'cosine' or (cats_gen == 'auto' and clustering == 'kmeans'):
        log.update({'generalization': 'none: vector-similarity based - maybe some day...'})
    else:
        log.update({'generalization': 'none: ' + str(cats_gen)})

    '''Learn grammar'''

    if grammar_rules != context:
        context = kwargs['context']
        kwargs['context'] = kwargs['grammar_rules']
        links, re06 = files2links(**kwargs)
        kwargs['context'] = context

    if 'disjuncts' not in 'categories':  # k-means, sparse agglomerative clustering
        categories = add_disjuncts(categories, links, **kwargs)  # category_learner.py

    # "fully connected rules": every cluster connected to all clusters  # 80825
    if kwargs['grammar_rules'] < 0:
        rules = deepcopy(categories)
        clusters = [i for i, x in enumerate(rules['cluster']) if i > 0 and x is not None]
        rule_list = [tuple([-x]) for x in clusters] + [tuple([x]) for x in clusters]
        for cluster in clusters:
            rules['disjuncts'][cluster] = set(rule_list)
    else:
        rules, re07 = induce_grammar(categories, **kwargs)

    lengths = [len(x) for x in rules['disjuncts']]
    if verbose in ['max', 'debug']:
        print('N clusters = len(rules[disjuncts]-1):', len(rules['disjuncts']) - 1)
        print('Rule set lengths:', lengths)

    '''Generalize grammar rules'''

    if 'rules_generalization' in kwargs:
        # if kwargs['rules_generalization'] not in ['', 'off']:
        if kwargs['rules_generalization'] in ['jaccard', 'legacy']:
            print('rules_generalization:', kwargs['rules_generalization'])
            rules, re08 = generalize_rules(rules, **kwargs)
            log.update(re08)
        elif kwargs['rules_generalization'] in ['hierarchical','new']:  # 81121
            print('generalise_rules ⇒ new')
            rules, re08 = generalise_rules(rules, **kwargs)
            log.update(re08)

    log['rule_sizes'] = Counter(
        [len(x) for i, x in enumerate(rules['words']) if rules['parent'][i] == 0])

    '''Save word category tree, Link Grammar files: cat_tree.txt, dict...dict'''

    re09 = save_cat_tree(rules, output_categories, verbose='none')
    # TODO: check file save error?
    log.update(re09)
    re10 = save_link_grammar(rules, output_grammar, grammar_rules)
    log.update(re10)
    log.update({'finish': str(UTC())})
    # TODO: elapsed execution time?  Save log?

    # 81120: check 2nd g12n   FIXME
    # rules, re11 = generalize_rules(rules, **kwargs)
    # re12 = save_cat_tree(rules, output_categories, verbose='none')
    # re13 = save_link_grammar(rules, output_grammar, grammar_rules)
    # log.update(re11)
    # log.update(re12)
    # log.update(re13)

    # return log
    return rules, log  # 81120 FIXME

# Notes:

# 80802: poc05.py/category_learner ⇒ category_learner.py/learn_categories
# 80825: random clusters, interconnected ⇒ cleanup, commit 80828
# 81021 cleanup: Grammar Learner 0.6
# 81102 sparse wordspace agglomerative clustering
