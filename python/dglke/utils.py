# -*- coding: utf-8 -*-
#
# setup.py
#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import math
import os
import argparse
import json

def get_compatible_batch_size(batch_size, neg_sample_size):
    if neg_sample_size < batch_size and batch_size % neg_sample_size != 0:
        old_batch_size = batch_size
        batch_size = int(math.ceil(batch_size / neg_sample_size) * neg_sample_size)
        print('batch size ({}) is incompatible to the negative sample size ({}). Change the batch size to {}'.format(
            old_batch_size, neg_sample_size, batch_size))
    return batch_size

def save_model(args, model):
    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)
    model.save_emb(args.save_path, args.dataset)

    # We need to save the model configurations as well.
    conf_file = os.path.join(args.save_path, 'config.json')
    with open(conf_file, 'w') as outfile:
        json.dump({'dataset': args.dataset,
                   'model': args.model_name,
                   'emb_size': args.hidden_dim,
                   'max_train_step': args.max_step,
                   'batch_size': args.batch_size,
                   'neg_sample_size': args.neg_sample_size,
                   'lr': args.lr,
                   'gamma': args.gamma,
                   'double_ent': args.double_ent,
                   'double_rel': args.double_rel,
                   'neg_adversarial_sampling': args.neg_adversarial_sampling,
                   'adversarial_temperature': args.adversarial_temperature,
                   'regularization_coef': args.regularization_coef,
                   'regularization_norm': args.regularization_norm},
                   outfile, indent=4)

class CommonArgParser(argparse.ArgumentParser):
    def __init__(self):
        super(CommonArgParser, self).__init__()

        self.add_argument('--model_name', default='TransE',
                          choices=['TransE', 'TransE_l1', 'TransE_l2', 'TransR',
                                   'RESCAL', 'DistMult', 'ComplEx', 'RotatE'],
                          help='The models provided by DGL-KE.')
        self.add_argument('--data_path', type=str, default='data',
                          help='The path of the directory where DGL-KE loads knowledge graph data.')
        self.add_argument('--dataset', type=str, default='FB15k',
                          help='The name of the knowledge graph stored under data_path. If it is one of'\
                                  'the builtin knowledge grpahs such as FB15k, DGL-KE will automatically'\
                                  'download the knowledge graph and keep it under data_path.')
        self.add_argument('--format', type=str, default='built_in',
                          help='The format of the dataset. For builtin knowledge graphs,'\
                                  'the foramt should be built_in. For users own knowledge graphs,'\
                                  'it needs to be raw_udd_{htr} or udd_{htr}.')
        self.add_argument('--data_files', type=str, default=None, nargs='+',
                          help='A list of data file names. This is used if users want to train KGE'\
                                  'on their own datasets. If the format is raw_udd_{htr},'\
                                  'users need to provide train_file [valid_file] [test_file].'\
                                  'If the format is udd_{htr}, users need to provide'\
                                  'entity_file relation_file train_file [valid_file] [test_file].'\
                                  'In both cases, valid_file and test_file are optional.')
        self.add_argument('--save_path', type=str, default='ckpts',
                          help='the path of the directory where models and logs are saved.')
        self.add_argument('--no_save_emb', action='store_true',
                          help='Disable saving the embeddings under save_path.')
        self.add_argument('--max_step', type=int, default=80000,
                          help='The maximal number of steps to train the model.'\
                                  'A step trains the model with a batch of data.')
        self.add_argument('--batch_size', type=int, default=1024,
                          help='The batch size for training.')
        self.add_argument('--batch_size_eval', type=int, default=8,
                          help='The batch size used for validation and test.')
        self.add_argument('--neg_sample_size', type=int, default=256,
                          help='The number of negative samples we use for each positive sample in the training.')
        self.add_argument('--neg_deg_sample', action='store_true',
                          help='Construct negative samples proportional to vertex degree in the training.'\
                                  'When this option is turned on, the number of negative samples per positive edge'\
                                  'will be doubled. Half of the negative samples are generated uniformly while'\
                                  'the other half are generated proportional to vertex degree.')
        self.add_argument('--neg_deg_sample_eval', action='store_true',
                          help='Construct negative samples proportional to vertex degree in the evaluation.')
        self.add_argument('--neg_sample_size_eval', type=int, default=-1,
                          help='The number of negative samples we use to evaluate a positive sample.')
        self.add_argument('--eval_percent', type=float, default=1,
                          help='Randomly sample some percentage of edges for evaluation.')
        self.add_argument('--no_eval_filter', action='store_true',
                          help='Disable filter positive edges from randomly constructed negative edges for evaluation')
        self.add_argument('-log', '--log_interval', type=int, default=1000000000,
                          help='Print runtime of different components every x steps.')
        self.add_argument('--eval_interval', type=int, default=10000,
                          help='Print evaluation results on the validation dataset every x steps'\
                                  'if validation is turned on')
        self.add_argument('--test', action='store_true',
                          help='Evaluate the model on the test set after the model is trained.')
        self.add_argument('--num_proc', type=int, default=1,
                          help='The number of processes to train the model in parallel.'\
                                  'In multi-GPU training, the number of processes by default is set to match the number of GPUs.'\
                                  'If set explicitly, the number of processes needs to be divisible by the number of GPUs.')
        self.add_argument('--num_thread', type=int, default=1,
                          help='The number of CPU threads to train the model in each process.'\
                                  'This argument is used for multiprocessing training.')
        self.add_argument('--force_sync_interval', type=int, default=-1,
                          help='We force a synchronization between processes every x steps for'\
                                  'multiprocessing training. This potentially stablizes the training process'
                                  'to get a better performance. For multiprocessing training, it is set to 1000 by default.')
        self.add_argument('--hidden_dim', type=int, default=400,
                          help='The embedding size of relation and entity')
        self.add_argument('--lr', type=float, default=0.01,
                          help='The learning rate. DGL-KE uses Adagrad to optimize the model parameters.')
        self.add_argument('-g', '--gamma', type=float, default=12.0,
                          help='The margin value in the score function. It is used by TransX and RotatE.')
        self.add_argument('-de', '--double_ent', action='store_true',
                          help='Double entitiy dim for complex number It is used by RotatE.')
        self.add_argument('-dr', '--double_rel', action='store_true',
                          help='Double relation dim for complex number.')
        self.add_argument('-adv', '--neg_adversarial_sampling', action='store_true',
                          help='Indicate whether to use negative adversarial sampling.'\
                                  'It will weight negative samples with higher scores more.')
        self.add_argument('-a', '--adversarial_temperature', default=1.0, type=float,
                          help='The temperature used for negative adversarial sampling.')
        self.add_argument('-rc', '--regularization_coef', type=float, default=0.000002,
                          help='The coefficient for regularization.')
        self.add_argument('-rn', '--regularization_norm', type=int, default=3,
                          help='norm used in regularization.')
