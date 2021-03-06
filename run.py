from __future__ import print_function, absolute_import
from reid.bottom_up import *
from reid import datasets
from reid import models
import numpy as np
import argparse
import os, sys, time
from reid.utils.logging import Logger
import os.path as osp
from torch.backends import cudnn
from datetime import datetime
import warnings

def main(args):
    cudnn.benchmark = True
    cudnn.enabled = True
    now=datetime.now()
    save_path = args.logs_dir

    os.mkdir(osp.join(args.logs_dir, '%s%s%s_%s%s%s'%(now.year, str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2), str(now.second).zfill(2))))
    sys.stdout = Logger(osp.join(args.logs_dir, '%s%s%s_%s%s%s/%s%s%s_%s%s%s.txt'%(now.year, str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2), str(now.second).zfill(2), now.year, str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2), str(now.second).zfill(2))))

    # get all unlabeled data for training
    dataset_all = datasets.create(args.dataset, osp.join(args.data_dir, args.dataset))
    new_train_data, cluster_id_labels = change_to_unlabel(dataset_all)
    num_train_ids = len(np.unique(np.array(cluster_id_labels)))
    nums_to_merge = int(num_train_ids * args.merge_percent)

    # nums_to_merge=3

    BuMain = Bottom_up(model_name=args.arch, batch_size=args.batch_size, 
            num_classes=num_train_ids,
            dataset=dataset_all,
            u_data=new_train_data, save_path=osp.join(args.logs_dir, '%s%s%s_%s%s%s'%(now.year, str(now.month).zfill(2), str(now.day).zfill(2), str(now.hour).zfill(2), str(now.minute).zfill(2), str(now.second).zfill(2))),
            max_frames=args.max_frames,
            embeding_fea_size=args.fea,
            bottom_up_real_negative=args.burn,
            ms_table=args.mst, 
            ms_real_negative=args.msrn)
    
    print('bottom_up_clustering_constraint: ', args.bucc)
    for step in range(int(1/args.merge_percent)-1):
        
        BuMain.train(new_train_data, step, loss=args.loss) 
        BuMain.evaluate(dataset_all.query, dataset_all.gallery)

        # get new train data for the next iteration
        print('----------------------------------------bottom-up clustering------------------------------------------------')
        if args.bucc: cluster_id_labels, new_train_data = BuMain.get_new_unique_constratint_train_data(cluster_id_labels, nums_to_merge, size_penalty=args.size_penalty)
        else: cluster_id_labels, new_train_data = BuMain.get_new_train_data(cluster_id_labels, nums_to_merge, size_penalty=args.size_penalty)


if __name__ == '__main__':
    warnings.filterwarnings("ignore")

    parser = argparse.ArgumentParser(description='bottom-up clustering')
    parser.add_argument('-d', '--dataset', type=str, default='PRW_BUformat',
                        choices=datasets.names())
    parser.add_argument('-b', '--batch-size', type=int, default=16)  
    parser.add_argument('-f', '--fea', type=int, default=2048)
    parser.add_argument('-a', '--arch', type=str, default='avg_pool',choices=models.names())
    working_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument('--data_dir', type=str, metavar='PATH',
                        default=os.path.join(working_dir,'../datasets'))
    # parser.add_argument('--logs_dir', type=str, metavar='PATH',
    #                     default=os.path.join(working_dir,'logs/PRW/bu'))
    # parser.add_argument('--logs_dir', type=str, metavar='PATH',
    #                     default=os.path.join(working_dir,'logs/PRW/ms'))
    # parser.add_argument('--logs_dir', type=str, metavar='PATH',
    #                     default=os.path.join(working_dir,'logs/PRW/all'))
    parser.add_argument('--logs_dir', type=str, metavar='PATH',
                        default=os.path.join(working_dir,'logs/tmp'))
    parser.add_argument('--max_frames', type=int, default=900)
    parser.add_argument('--loss', type=str, default='ExLoss')
    parser.add_argument('-m', '--momentum', type=float, default=0.5)
    parser.add_argument('-s', '--step_size', type=int, default=55)
    parser.add_argument('--size_penalty',type=float, default=0.005)
    parser.add_argument('-mp', '--merge_percent',type=float, default=0.05)
    parser.add_argument('--bucc', help='bottom_up_clustering_constraint')
    parser.add_argument('--burn', help='bottom_up_real_negative')
    parser.add_argument('--mst', help='ms_table')
    parser.add_argument('--msrn', help='ms_real_negative')
    main(parser.parse_args())
    

